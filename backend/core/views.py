import json
import uuid
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from .models import Campaign, Membership, RulesetVersion, Character, Submission, Review, Invite, RuleDecision, Asset, AuditEvent
from .serializers import CharacterDataSerializer
from .rules import calculate, DEFAULT_CATALOG, SOURCE_HASH, ARCHETYPES, roll_attribute


def body(request):
    try:
        data = json.loads(request.body or '{}')
    except (ValueError, UnicodeDecodeError):
        raise ValidationError('JSON inválido.')
    if not isinstance(data, dict):
        raise ValidationError('Esperado objeto JSON.')
    return data


def csrf_failure(request, reason=''):
    return JsonResponse({'detail': 'Sessão de segurança inválida. Atualize a página e entre novamente.'}, status=403)


@ensure_csrf_cookie
@require_http_methods(['GET'])
def session(request):
    return JsonResponse({'user': {'id': request.user.id, 'name': request.user.username} if request.user.is_authenticated else None})


@csrf_protect
@require_http_methods(['POST'])
def auth(request, action):
    try:
        if action != 'logout':
            throttle_key = 'auth:' + request.META.get('REMOTE_ADDR', 'unknown')
            attempts = cache.get(throttle_key, 0)
            if attempts >= 20:
                return JsonResponse({'detail': 'Muitas tentativas. Aguarde um minuto.'}, status=429)
            cache.set(throttle_key, attempts + 1, timeout=60)
        data = body(request)
        if action == 'logout':
            logout(request)
            return JsonResponse({'ok': True})
        username, password = data.get('username', ''), data.get('password', '')
        if not isinstance(username, str) or not isinstance(password, str) or not 3 <= len(username) <= 100 or len(password) > 256:
            raise ValidationError('Informe usuário de 3 a 100 caracteres e senha válida.')
        if action == 'register':
            user = get_user_model()(username=username)
            validate_password(password, user=user)
            if get_user_model().objects.filter(username=username).exists():
                return JsonResponse({'detail': 'Nome de usuário indisponível.'}, status=400)
            user.set_password(password)
            try:
                with transaction.atomic():
                    user.save()
            except IntegrityError:
                # A segunda inscrição pode ultrapassar o exists() antes do commit.
                if get_user_model().objects.filter(username=username).exists():
                    return JsonResponse({'detail': 'Nome de usuário indisponível.'}, status=400)
                raise
        elif action == 'login':
            user = authenticate(request, username=username, password=password)
            if user is None:
                return JsonResponse({'detail': 'Usuário ou senha inválidos.'}, status=400)
        else:
            return JsonResponse({'detail': 'Operação inexistente.'}, status=404)
        login(request, user)
        return JsonResponse({'user': {'id': user.id, 'name': user.username}})
    except ValidationError as error:
        return JsonResponse({'detail': ' '.join(error.messages)}, status=400)


def accessible_campaigns(user):
    return Campaign.objects.filter(Q(master=user) | Q(membership__user=user)).distinct()


def campaign_for(user, pk, master=False, lock=False):
    if type(pk) is not int or pk <= 0:
        raise NotFound('Campanha não encontrada.')
    campaign = get_object_or_404(accessible_campaigns(user), pk=pk)
    if lock:
        # Evita FOR UPDATE no DISTINCT do filtro de permissões.
        campaign = get_object_or_404(Campaign.objects.select_for_update(), pk=campaign.pk)
    if master and campaign.master_id != user.id:
        raise PermissionDenied('Somente o mestre desta campanha.')
    return campaign


def character_for(user, pk, owner=False, lock=False):
    try:
        pk = uuid.UUID(str(pk))
    except (ValueError, TypeError, AttributeError):
        raise NotFound('Ficha não encontrada.')
    query = Character.objects.filter(campaign__in=accessible_campaigns(user)).filter(Q(owner=user) | Q(campaign__master=user))
    character = get_object_or_404(query, pk=pk)
    if owner and character.owner_id != user.id:
        raise PermissionDenied('Somente o dono pode editar a ficha.')
    if lock:
        # Ordem única: campanha -> ficha. Decisões globais usam a mesma campanha.
        campaign_for(user, character.campaign_id, lock=True)
        character = get_object_or_404(query.select_for_update(of=('self',)), pk=pk)
    return character


def decisions_for(character):
    records = RuleDecision.objects.filter(campaign=character.campaign).filter(
        Q(character__isnull=True) | Q(character=character, applies_revision=character.revision)).order_by('id')
    latest = {}
    for record in records:
        latest[record.rule_id] = record
    return {key: value.value for key, value in latest.items()}, [
        {'id': d.id, 'ruleId': d.rule_id, 'value': d.value, 'reason': d.reason,
         'authorId': d.author_id, 'createdAt': d.created_at.isoformat()} for d in latest.values()]


def summary(character):
    decisions, decision_records = decisions_for(character)
    report = calculate(character.data, decisions)
    submissions = []
    approved = False
    for sub in character.submissions.select_related('review').order_by('-id'):
        review = getattr(sub, 'review', None)
        current = sub.revision == character.revision and sub.decisions == decision_records
        approved |= bool(review and review.status == 'approved' and current)
        submissions.append({'id': sub.id, 'revision': sub.revision, 'snapshot': sub.snapshot,
            'report': sub.report, 'current': current, 'createdAt': sub.created_at.isoformat(),
            'review': {'status': review.status, 'comment': review.comment} if review else None})
    return {'id': str(character.id), 'campaignId': character.campaign_id, 'ownerId': character.owner_id,
            'rulesetVersion': character.ruleset_id, 'revision': character.revision, 'data': character.data,
            'resources': character.resources, 'report': report, 'decisions': decision_records,
            'approved': approved, 'submissions': submissions}


def audit(request, action, character):
    AuditEvent.objects.create(author=request.user, action=action, entity=str(character.id), revision=character.revision)


@api_view(['GET', 'POST'])
def campaigns(request):
    if request.method == 'POST':
        name = request.data.get('name')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
            return Response({'detail': 'Informe nome de campanha até 120 caracteres.'}, status=400)
        with transaction.atomic():
            rules = RulesetVersion.objects.create(source_hash=SOURCE_HASH, catalog=DEFAULT_CATALOG)
            campaign = Campaign.objects.create(name=name.strip(), master=request.user, ruleset=rules)
            Membership.objects.create(campaign=campaign, user=request.user)
        return Response({'id': campaign.id, 'name': campaign.name, 'role': 'master'}, status=201)
    return Response([{'id': c.id, 'name': c.name, 'role': 'master' if c.master_id == request.user.id else 'player',
                      'rulesetVersion': c.ruleset_id} for c in accessible_campaigns(request.user)])


@api_view(['GET'])
def catalog(request, pk):
    campaign = campaign_for(request.user, pk)
    return Response({**campaign.ruleset.catalog, 'rulesetVersion': campaign.ruleset_id,
        'sourceSha256': campaign.ruleset.source_hash,
        'assets': [{'id': a.id, 'label': a.label} for a in Asset.objects.filter(campaign=campaign, approved=True)]})


@api_view(['POST'])
def invites(request, pk):
    campaign = campaign_for(request.user, pk, master=True)
    invite = Invite.objects.create(campaign=campaign, expires_at=timezone.now() + timedelta(days=7))
    return Response({'token': invite.token, 'expiresAt': invite.expires_at.isoformat()}, status=201)


@api_view(['POST'])
@transaction.atomic
def join(request):
    token = request.data.get('token')
    if not isinstance(token, str) or len(token) > 64:
        return Response({'detail': 'Convite inválido.'}, status=400)
    invite = get_object_or_404(Invite.objects.select_for_update(), token=token, consumed=False, expires_at__gt=timezone.now())
    Membership.objects.get_or_create(campaign=invite.campaign, user=request.user)
    invite.used_by = request.user
    invite.consumed = True
    invite.save()
    return Response({'campaignId': invite.campaign_id})


@api_view(['GET', 'POST'])
@transaction.atomic
def characters(request):
    if request.method == 'GET':
        return Response([summary(c) for c in Character.objects.filter(campaign__in=accessible_campaigns(request.user)).filter(
            Q(owner=request.user) | Q(campaign__master=request.user)).order_by('-updated_at')])
    campaign = campaign_for(request.user, request.data.get('campaignId'), lock=True)
    serializer = CharacterDataSerializer(data=request.data.get('data', {}))
    serializer.is_valid(raise_exception=True)
    validate_asset(campaign, serializer.validated_data)
    character = Character.objects.create(owner=request.user, campaign=campaign, ruleset=campaign.ruleset, data=serializer.validated_data)
    audit(request, 'character.created', character)
    return Response(summary(character), status=201)


def validate_asset(campaign, data):
    if data.get('assetId') is not None:
        get_object_or_404(Asset, pk=data['assetId'], campaign=campaign, approved=True)


@api_view(['GET', 'PATCH'])
@transaction.atomic
def character_detail(request, pk):
    character = character_for(request.user, pk, owner=request.method == 'PATCH', lock=request.method == 'PATCH')
    if request.method == 'PATCH':
        if type(request.data.get('revision')) is not int or request.data['revision'] != character.revision:
            return Response({'detail': 'Outra alteração foi salva. Sua edição foi preservada; recarregue para comparar.',
                             'current': summary(character)}, status=409)
        serializer = CharacterDataSerializer(data=request.data.get('data', {}))
        serializer.is_valid(raise_exception=True)
        validate_asset(character.campaign, serializer.validated_data)
        character.data = serializer.validated_data
        character.revision += 1
        character.save()
        audit(request, 'character.updated', character)
    return Response(summary(character))


@api_view(['POST'])
def preview(request):
    campaign = campaign_for(request.user, request.data.get('campaignId'))
    serializer = CharacterDataSerializer(data=request.data.get('data', {}))
    serializer.is_valid(raise_exception=True)
    temporary = Character(campaign=campaign, revision=0)
    character_id = request.data.get('characterId')
    if character_id:
        existing = character_for(request.user, character_id)
        if existing.campaign_id != campaign.id:
            raise PermissionDenied()
        # Validações específicas só se aplicam à revisão exatamente conferida.
        if existing.data == serializer.validated_data:
            temporary = existing
    decisions, _ = decisions_for(temporary)
    return Response(calculate(serializer.validated_data, decisions))


@api_view(['POST'])
def comparisons(request):
    campaign_for(request.user, request.data.get('campaignId'))
    serializer = CharacterDataSerializer(data=request.data.get('data', {}))
    serializer.is_valid(raise_exception=True)
    return Response([{'archetype': a, 'report': calculate({**serializer.validated_data, 'archetypeId': a['id']})} for a in ARCHETYPES])


@api_view(['POST'])
@transaction.atomic
def submit(request, pk):
    character = character_for(request.user, pk, owner=True, lock=True)
    if type(request.data.get('revision')) is not int or request.data['revision'] != character.revision:
        return Response({'detail': 'A ficha mudou; atualize antes de enviar.'}, status=409)
    decisions, records = decisions_for(character)
    report = calculate(character.data, decisions)
    if report['errors']:
        return Response({'detail': 'Corrija os atributos inválidos antes de enviar.', 'report': report}, status=400)
    old_revision = character.revision
    character.revision += 1
    character.save()
    # As validações individuais acompanham apenas o snapshot idêntico enviado.
    RuleDecision.objects.filter(character=character, applies_revision=old_revision).update(applies_revision=character.revision)
    Submission.objects.create(character=character, revision=character.revision, snapshot=character.data,
                              report=report, decisions=records, author=request.user)
    audit(request, 'character.submitted', character)
    return Response(summary(character), status=201)


@api_view(['POST'])
@transaction.atomic
def reviews(request, pk):
    submission = get_object_or_404(Submission.objects.select_related('character__campaign'), pk=pk)
    character = character_for(request.user, submission.character_id, lock=True)
    campaign_for(request.user, character.campaign_id, master=True)
    status, comment = request.data.get('status'), request.data.get('comment', '')
    if status not in ('approved', 'changes') or not isinstance(comment, str) or len(comment) > 8000:
        return Response({'detail': 'Revisão inválida.'}, status=400)
    if status == 'changes' and not comment.strip():
        return Response({'detail': 'Descreva os ajustes solicitados.'}, status=400)
    _, records = decisions_for(character)
    if submission.revision != character.revision or submission.decisions != records:
        return Response({'detail': 'Snapshot desatualizado. Solicite um novo envio.'}, status=409)
    if status == 'approved' and not submission.report['canApprove']:
        return Response({'detail': 'Resolva as pendências e peça novo envio antes de aprovar.'}, status=400)
    if Review.objects.filter(submission=submission).exists():
        return Response({'detail': 'Esta revisão já foi concluída. Solicite novo envio.'}, status=409)
    Review.objects.create(submission=submission, reviewer=request.user, status=status, comment=comment)
    audit(request, 'review.' + status, character)
    return Response(summary(character))


@api_view(['POST'])
@transaction.atomic
def decision(request, pk):
    campaign = campaign_for(request.user, pk, master=True, lock=True)
    rule_id, value, reason = request.data.get('ruleId'), request.data.get('value'), request.data.get('reason')
    character_id = request.data.get('characterId')
    if rule_id not in ('R03', 'R06', 'R08', 'R09', 'RACE', 'TECHNIQUES', 'ATIRADOR') or not isinstance(value, dict) or not isinstance(reason, str) or not reason.strip() or len(reason) > 4000 or len(json.dumps(value)) > 8000:
        return Response({'detail': 'Informe regra permitida, decisão estruturada e motivo.'}, status=400)
    character = None
    if rule_id in ('RACE', 'TECHNIQUES', 'ATIRADOR'):
        character = character_for(request.user, character_id, lock=True)
        if character.campaign_id != campaign.id:
            raise PermissionDenied()
        if rule_id == 'ATIRADOR':
            valid = type(value.get('allowRespiration')) is bool
        else:
            valid = type(value.get('validated')) is bool
        if not valid:
            return Response({'detail': 'Valor deve conter confirmação booleana.'}, status=400)
    elif rule_id == 'R09' and (type(value.get('spendAll')) is not bool or not value.get('hybridLimit')):
        return Response({'detail': 'R09 exige spendAll booleano e hybridLimit.'}, status=400)
    elif rule_id == 'R06' and not all(value.get(k) is not None for k in ('mainSkillExtra', 'duplicates', 'trainingGrades')):
        return Response({'detail': 'R06 exige mainSkillExtra, duplicates e trainingGrades.'}, status=400)
    elif rule_id == 'R08' and not value.get('eligibility'):
        return Response({'detail': 'R08 exige eligibility.'}, status=400)
    record = RuleDecision.objects.create(campaign=campaign, character=character, applies_revision=character.revision if character else None,
        rule_id=rule_id, value=value, reason=reason, author=request.user)
    AuditEvent.objects.create(author=request.user, action='rule.decided', entity=str(record.id))
    return Response({'id': record.id}, status=201)


@api_view(['PATCH'])
@transaction.atomic
def resources(request, pk):
    character = character_for(request.user, pk, owner=True, lock=True)
    values = request.data
    if not isinstance(values, dict) or set(values) != {'pv', 'pe', 'san'} or any(type(v) is not int or not 0 <= v <= 100000 for v in values.values()):
        return Response({'detail': 'Informe PV, PE e sanidade atuais inteiros não negativos.'}, status=400)
    character.resources = values
    character.save(update_fields=['resources', 'updated_at'])
    audit(request, 'resources.updated', character)
    return Response(summary(character))


@api_view(['GET'])
def export(request, pk):
    character = character_for(request.user, pk)
    result = summary(character)
    response = Response({'schemaVersion': 1, 'rulesetVersion': character.ruleset_id, 'sourceSha256': character.ruleset.source_hash,
        'exportedAt': timezone.now().isoformat(), 'character': result['data'], 'resourceState': result['resources'],
        'revision': result['revision'], 'approved': result['approved'], 'validation': result['report'],
        'decisions': result['decisions'], 'sourceRefs': result['report']['explanations']})
    response['Content-Disposition'] = 'attachment; filename="personagem.json"'
    return response


@api_view(['GET'])
def asset_content(request, pk):
    asset = get_object_or_404(Asset, pk=pk, approved=True, campaign__in=accessible_campaigns(request.user))
    response = FileResponse(asset.file.open('rb'), as_attachment=True, filename='token.png')
    response['Cache-Control'] = 'private, no-store'
    return response


@api_view(['POST'])
def roll(request):
    try:
        return Response(roll_attribute(request.data.get('attribute')))
    except ValueError as error:
        return Response({'detail': str(error)}, status=400)
