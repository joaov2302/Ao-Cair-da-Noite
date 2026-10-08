from copy import deepcopy
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from .models import Campaign, Membership, RulesetVersion, Character, Submission, Review, RuleDecision, Invite, Asset, AuditEvent
from .rules import DEFAULT_CATALOG, SOURCE_HASH, calculate, roll_attribute


def draft(**changes):
    return {'name': 'Personagem de teste', 'race': 'Raça manual', 'classId': 'samurai', 'archetypeId': 'guerreiro',
            'attributes': dict(zip(('FOR', 'AGI', 'VIG', 'PRE', 'INT'), (3, 3, 1, 1, 1))), **changes}


class RulesTests(TestCase):
    def test_initial_comparison_uses_same_inputs(self):
        expected = {'guerreiro': (21, 4, 12), 'lutador': (17, 5, 12), 'sensitivo': (13, 4, 12), 'suporte': (11, 5, 15)}
        for archetype, values in expected.items():
            report = calculate(draft(archetypeId=archetype))
            self.assertEqual(tuple(report['maxima'].values()), values)
            self.assertEqual(report['explanations'][0]['inputs'], {'VIG': 1})
            self.assertEqual(report['explanations'][0]['sourceSha256'], SOURCE_HASH)

    def test_attribute_edge_cases_and_incomplete_draft(self):
        for distribution in ((2, 2, 2, 2, 1), (0, 3, 3, 2, 1)):
            report = calculate(draft(attributes=dict(zip(('FOR', 'AGI', 'VIG', 'PRE', 'INT'), distribution))))
            self.assertEqual(report['errors'], [])
        for value in (-1, 1.5, 4, None, True):
            attributes = draft()['attributes']; attributes['VIG'] = value
            self.assertTrue(calculate(draft(attributes=attributes))['errors'])
        partial = calculate(draft(attributes=dict(zip(('FOR', 'AGI', 'VIG', 'PRE', 'INT'), (2, 2, 2, 1, 1)))))
        self.assertEqual(partial['errors'], [])
        self.assertFalse(partial['canApprove'])
        self.assertTrue(partial['warnings'])

    def test_attribute_zero_selects_lowest_two_dice(self):
        self.assertEqual(roll_attribute(0, [19, 2])['result'], 2)
        self.assertEqual(roll_attribute(0, [7, 7])['result'], 7)
        self.assertEqual(roll_attribute(3, [1, 20, 4])['result'], 20)
        with self.assertRaises(ValueError):
            roll_attribute(0, [10])

    def test_shooter_respiration_requires_specific_exception(self):
        report = calculate(draft(classId='atirador', techniqueKind='respiracao'))
        self.assertIn('ATIRADOR', [p['id'] for p in report['pending']])
        report = calculate(draft(classId='atirador', techniqueKind='respiracao'), {'ATIRADOR': {'allowRespiration': True}})
        self.assertNotIn('ATIRADOR', [p['id'] for p in report['pending']])


class ApiTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.master = User.objects.create_user('mestre-teste', password='Senha-Teste-2026!')
        self.player = User.objects.create_user('jogador-teste', password='Senha-Teste-2026!')
        self.other = User.objects.create_user('outro-teste', password='Senha-Teste-2026!')
        self.rules = RulesetVersion.objects.create(source_hash=SOURCE_HASH, catalog=DEFAULT_CATALOG)
        self.campaign = Campaign.objects.create(name='Mesa de teste', master=self.master, ruleset=self.rules)
        Membership.objects.create(campaign=self.campaign, user=self.player)
        self.character = Character.objects.create(owner=self.player, campaign=self.campaign, ruleset=self.rules, data=draft())
        self.client = APIClient()
        self.client.force_login(self.player)
        self.url = f'/api/characters/{self.character.id}'

    def post(self, url, data):
        return self.client.post(url, data, format='json')

    def resolve(self):
        self.client.force_login(self.master)
        for rule, value in [('R06', {'mainSkillExtra': True, 'duplicates': 'Escolha outra', 'trainingGrades': 'Validação manual'}),
                            ('R08', {'eligibility': 'Sem técnica nesta ficha'}),
                            ('R09', {'spendAll': True, 'hybridLimit': 'Benefícios manuais'}),
                            ('RACE', {'validated': True})]:
            result = self.post(f'/api/campaigns/{self.campaign.id}/decisions',
                {'ruleId': rule, 'value': value, 'reason': 'Decisão sintética apenas para este teste.', 'characterId': str(self.character.id)})
            self.assertEqual(result.status_code, 201, result.data)
        self.client.force_login(self.player)

    def submit(self):
        self.character.refresh_from_db()
        result = self.post(self.url + '/submissions', {'revision': self.character.revision})
        self.assertEqual(result.status_code, 201, result.data)
        return result.data['submissions'][0]['id']

    def test_private_characters_are_scoped_even_in_same_campaign(self):
        Membership.objects.create(campaign=self.campaign, user=self.other)
        self.client.force_login(self.other)
        for suffix in ('', '/export'):
            self.assertEqual(self.client.get(self.url + suffix).status_code, 404)
        self.assertEqual(self.client.get('/api/characters').data, [])
        result = self.client.patch(self.url, {'revision': 1, 'data': draft(name='Alterado')}, format='json')
        self.assertEqual(result.status_code, 404)
        self.character.refresh_from_db();self.assertEqual(self.character.data['name'], 'Personagem de teste')

    def test_foreign_master_cannot_review_submission(self):
        submission = self.submit()
        foreign = Campaign.objects.create(name='Outra mesa', master=self.other, ruleset=self.rules)
        self.client.force_login(self.other)
        result = self.post(f'/api/submissions/{submission}/reviews', {'status': 'approved', 'comment': ''})
        self.assertEqual(result.status_code, 404)
        self.assertEqual(Review.objects.count(), 0)

    def test_snapshot_approval_changes_and_resources(self):
        self.resolve();submission_id = self.submit()
        self.client.force_login(self.master)
        approved = self.post(f'/api/submissions/{submission_id}/reviews', {'status': 'approved', 'comment': 'Conferido.'})
        self.assertEqual(approved.status_code, 200, approved.data)
        self.assertTrue(approved.data['approved'])
        self.client.force_login(self.player)
        current_revision = approved.data['revision']
        result = self.client.patch(self.url + '/resources', {'pv': 7, 'pe': 2, 'san': 8}, format='json')
        self.assertEqual(result.data['revision'], current_revision)
        self.assertTrue(result.data['approved'])
        self.assertEqual(result.data['report']['maxima']['pv'], 21)
        result = self.client.patch(self.url, {'revision': current_revision, 'data': draft(name='Novo nome')}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.data['approved'])
        submission = Submission.objects.get(pk=submission_id)
        self.assertEqual(submission.snapshot['name'], 'Personagem de teste')
        self.assertEqual(submission.snapshot['attributes']['VIG'], 1)
        self.assertIn('RACE', [p['id'] for p in result.data['report']['pending']])

    def test_pending_snapshot_cannot_be_approved(self):
        submission_id = self.submit()
        self.client.force_login(self.master)
        response = self.post(f'/api/submissions/{submission_id}/reviews', {'status': 'approved'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Review.objects.count(), 0)
        response = self.post(f'/api/submissions/{submission_id}/reviews', {'status': 'changes', 'comment': 'Defina a raça.'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['approved'])

    def test_new_campaign_decision_invalidates_approval(self):
        self.resolve();submission_id = self.submit()
        self.client.force_login(self.master)
        self.post(f'/api/submissions/{submission_id}/reviews', {'status': 'approved'})
        self.post(f'/api/campaigns/{self.campaign.id}/decisions', {'ruleId': 'R08', 'value': {'eligibility': 'Decisão alterada'}, 'reason': 'Teste.'})
        self.assertFalse(self.client.get(self.url).data['approved'])

    def test_conflict_preserves_saved_data(self):
        saved = self.client.patch(self.url, {'revision': 1, 'data': draft(name='Primeira edição')}, format='json')
        self.assertEqual(saved.status_code, 200)
        stale = self.client.patch(self.url, {'revision': 1, 'data': draft(name='Edição antiga')}, format='json')
        self.assertEqual(stale.status_code, 409)
        self.character.refresh_from_db();self.assertEqual(self.character.data['name'], 'Primeira edição')

    def test_protected_fields_and_invalid_attributes_rejected(self):
        for changes in ({'ownerId': self.other.id}, {'approved': True}, {'attributes': {'VIG': 1.5}}, {'attributes': {'VIG': True}}):
            response = self.client.patch(self.url, {'revision': 1, 'data': draft(**changes)}, format='json')
            self.assertEqual(response.status_code, 400, response.data)
        self.character.refresh_from_db();self.assertEqual(self.character.revision, 1)

    def test_only_master_can_decide(self):
        response = self.post(f'/api/campaigns/{self.campaign.id}/decisions', {'ruleId': 'RACE', 'value': {'validated': True}, 'reason': 'Tentativa.', 'characterId': str(self.character.id)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(RuleDecision.objects.count(), 0)

    def test_invites_are_expiring_single_use(self):
        self.client.force_login(self.master)
        invite = self.post(f'/api/campaigns/{self.campaign.id}/invites', {}).data
        self.client.force_login(self.other)
        self.assertEqual(self.post('/api/join', {'token': invite['token']}).status_code, 200)
        self.assertEqual(self.post('/api/join', {'token': invite['token']}).status_code, 404)
        expired = Invite.objects.create(campaign=self.campaign, expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post('/api/join', {'token': expired.token}).status_code, 404)

    def test_export_contains_version_pending_sources_and_current_resources(self):
        result = self.client.get(self.url+'/export', HTTP_ACCEPT='text/html,application/xhtml+xml,*/*;q=0.8')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result['Content-Type'].startswith('application/json'))
        self.assertEqual(result.data['schemaVersion'], 1)
        self.assertEqual(result.data['sourceSha256'], SOURCE_HASH)
        self.assertTrue(result.data['validation']['pending'])
        self.assertFalse(result.data['approved'])

    def test_private_sources_and_unapproved_assets_are_not_served(self):
        private = Asset.objects.create(campaign=self.campaign, label='Teste', approved=False, sha256='a'*64, file='private.png')
        self.assertEqual(self.client.get(f'/api/assets/{private.id}/content').status_code, 404)
        self.assertEqual(self.client.get('/Contexto/Privado/Livros/Ao%20Cair%20da%20Noite.docx').status_code, 404)

    def test_preview_accepts_draft_without_approval(self):
        result = self.post('/api/characters/preview', {'campaignId': self.campaign.id, 'data': draft()})
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['maxima']['pv'], 21)
        self.assertFalse(result.data['canApprove'])

    def test_ruleset_cannot_be_changed_in_place(self):
        self.rules.label = 'Alterado'
        with self.assertRaises(ValueError):
            self.rules.save()

    def test_audit_failure_rolls_back_each_character_mutation(self):
        self.resolve()
        submission_id = self.submit()
        self.character.refresh_from_db()
        revision = self.character.revision
        operations = [
            (self.player, 'post', '/api/characters', {'campaignId': self.campaign.pk, 'data': draft()}),
            (self.player, 'patch', self.url, {'revision': revision, 'data': draft(name='Não deve persistir')}),
            (self.player, 'patch', self.url + '/resources', {'pv': 1, 'pe': 2, 'san': 3}),
            (self.player, 'post', self.url + '/submissions', {'revision': revision}),
            (self.master, 'post', f'/api/submissions/{submission_id}/reviews', {'status': 'approved'}),
            (self.master, 'post', f'/api/campaigns/{self.campaign.pk}/decisions',
                {'ruleId': 'R08', 'value': {'eligibility': 'Não deve persistir'}, 'reason': 'Teste.'}),
        ]
        models = (Character, Submission, Review, RuleDecision, AuditEvent)
        before = [list(model.objects.order_by('pk').values()) for model in models]
        for user, method, url, data in operations:
            with self.subTest(url=url, method=method):
                self.client.force_login(user)
                with patch('core.views.AuditEvent.objects.create', side_effect=RuntimeError('Falha sintética de auditoria')):
                    with self.assertRaisesMessage(RuntimeError, 'Falha sintética de auditoria'):
                        getattr(self.client, method)(url, data, format='json')
                self.assertEqual([list(model.objects.order_by('pk').values()) for model in models], before)

    def test_csrf_is_enforced_before_login_and_registration(self):
        client = Client(enforce_csrf_checks=True)
        payload = {'username': 'csrf-teste', 'password': 'Senha-Teste-2026!'}
        self.assertEqual(client.post('/api/auth/login', payload, content_type='application/json').status_code, 403)
        self.assertEqual(client.post('/api/auth/register', payload, content_type='application/json').status_code, 403)
        client.get('/api/session')
        token = client.cookies['csrftoken'].value
        rejected = client.post('/api/auth/login', payload, content_type='application/json', HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://outro-dominio.invalid')
        self.assertEqual(rejected.status_code, 403)
        response = client.post('/api/auth/login', {'username': 'jogador-teste', 'password': 'Senha-Teste-2026!'}, content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(client.cookies['csrftoken'].value, token)
        self.assertEqual(client.post('/api/campaigns', {'name': 'Teste'}, content_type='application/json').status_code, 403)
