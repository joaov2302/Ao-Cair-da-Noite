"""Transações reais em conexões independentes; não equivalem a um piloto da mesa."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from time import monotonic
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from . import views
from .models import AuditEvent, Campaign, Character, Invite, Membership, Review, RuleDecision, RulesetVersion, Submission
from .rules import DEFAULT_CATALOG, SOURCE_HASH
from .tests import draft


@skipUnless(connection.vendor == 'postgresql', 'Concorrência exige PostgreSQL real.')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.master = User.objects.create_user('mestre-concorrencia', password='Teste-2026!')
        self.player = User.objects.create_user('jogador-concorrencia', password='Teste-2026!')
        self.other = User.objects.create_user('outro-concorrencia', password='Teste-2026!')
        rules = RulesetVersion.objects.create(source_hash=SOURCE_HASH, catalog=DEFAULT_CATALOG)
        self.campaign = Campaign.objects.create(name='Mesa sintética concorrente', master=self.master, ruleset=rules)
        Membership.objects.create(campaign=self.campaign, user=self.player)
        self.character = Character.objects.create(owner=self.player, campaign=self.campaign, ruleset=rules, data=draft())
        self.url = f'/api/characters/{self.character.pk}'

    def request(self, user, method, url, data):
        client = APIClient()
        if user:
            client.force_authenticate(user)
        return getattr(client, method)(url, data, format='json')

    def parallel(self, *calls):
        barrier = Barrier(len(calls))

        def worker(call):
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid(), current_database()')
                    pid, database = cursor.fetchone()
                barrier.wait(timeout=10)
                result = call()
                return pid, database, result
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(calls)) as pool:
            futures = [pool.submit(worker, call) for call in calls]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(len({pid for pid, _, _ in results}), len(calls))
        for _, database, _ in results:
            self.assertTrue(database.startswith('test_acdn_api_'), database)
        return [result for _, _, result in results]

    def resolve(self):
        for rule, value in [('R06', {'mainSkillExtra': True, 'duplicates': 'Outra', 'trainingGrades': 'Manual'}),
                            ('R08', {'eligibility': 'Sintética'}),
                            ('R09', {'spendAll': True, 'hybridLimit': 'Manual'}), ('RACE', {'validated': True})]:
            response = self.request(self.master, 'post', f'/api/campaigns/{self.campaign.pk}/decisions',
                                    {'ruleId': rule, 'value': value, 'reason': 'Somente teste.', 'characterId': str(self.character.pk)})
            self.assertEqual(response.status_code, 201)

    def submit(self):
        response = self.request(self.player, 'post', self.url + '/submissions', {'revision': 1})
        self.assertEqual(response.status_code, 201)
        return response.data['submissions'][0]['id']

    def test_two_edits_have_one_winner_and_one_conflict(self):
        responses = self.parallel(*[lambda name=name: self.request(self.player, 'patch', self.url,
                                  {'revision': 1, 'data': draft(name=name)}) for name in ['Primeira', 'Segunda']])
        self.assertEqual(sorted(r.status_code for r in responses), [200, 409])
        winner = next(r for r in responses if r.status_code == 200)
        loser = next(r for r in responses if r.status_code == 409)
        self.character.refresh_from_db()
        self.assertEqual(self.character.revision, 2)
        self.assertEqual(self.character.data, winner.data['data'])
        self.assertEqual(loser.data['current']['data'], winner.data['data'])
        self.assertEqual(AuditEvent.objects.filter(action='character.updated').count(), 1)

    def test_one_invite_two_users_has_one_consumption(self):
        invite = Invite.objects.create(campaign=self.campaign, expires_at=timezone.now() + timedelta(days=1))
        responses = self.parallel(*[lambda user=user: self.request(user, 'post', '/api/join', {'token': invite.token})
                                    for user in [self.master, self.other]])
        self.assertEqual(sorted(r.status_code for r in responses), [200, 404])
        invite.refresh_from_db()
        self.assertTrue(invite.consumed)
        self.assertEqual(Membership.objects.filter(campaign=self.campaign, user__in=[self.master, self.other]).count(), 1)
        self.assertTrue(Membership.objects.filter(campaign=self.campaign, user_id=invite.used_by_id).exists())

    def test_double_submission_preserves_one_snapshot(self):
        responses = self.parallel(*[lambda: self.request(self.player, 'post', self.url + '/submissions', {'revision': 1})] * 2)
        self.assertEqual(sorted(r.status_code for r in responses), [201, 409])
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='character.submitted').count(), 1)
        self.character.refresh_from_db()
        self.assertEqual(self.character.revision, 2)
        self.assertEqual(Submission.objects.get().snapshot, self.character.data)

    def test_two_reviews_preserve_one_verdict_and_audit(self):
        self.resolve()
        submission = self.submit()
        responses = self.parallel(*[lambda: self.request(self.master, 'post', f'/api/submissions/{submission}/reviews',
                                    {'status': 'approved', 'comment': 'Teste.'})] * 2)
        self.assertEqual(sorted(r.status_code for r in responses), [200, 409])
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action='review.approved').count(), 1)

    def test_simultaneous_duplicate_registration_returns_controlled_error(self):
        insert_barrier = Barrier(2)

        def register():
            def synchronize(execute, sql, params, many, context):
                if sql.startswith('INSERT INTO "auth_user"'):
                    insert_barrier.wait(timeout=10)
                return execute(sql, params, many, context)
            with connection.execute_wrapper(synchronize):
                return self.request(None, 'post', '/api/auth/register',
                                    {'username': 'duplicado-sintetico', 'password': 'Caderno-Teste-2026!'})

        responses = self.parallel(register, register)
        self.assertEqual(sorted(r.status_code for r in responses), [200, 400])
        rejected = next(r for r in responses if r.status_code == 400)
        self.assertEqual(rejected.json(), {'detail': 'Nome de usuário indisponível.'})
        self.assertEqual(get_user_model().objects.filter(username='duplicado-sintetico').count(), 1)

    def wait_for_lock(self, pid):
        deadline = monotonic() + 8
        while monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [pid])
                row = cursor.fetchone()
            if row and row[0] == 'Lock':
                return
            Event().wait(0.02)
        self.fail('A conexão concorrente não aguardou bloqueio real no PostgreSQL.')

    def test_approval_first_then_global_decision_invalidates_exact_snapshot(self):
        self.resolve()
        submission = self.submit()
        observed, release, ready = Event(), Event(), Event()
        real_decisions = views.decisions_for
        pids = {}

        def held_decisions(character):
            result = real_decisions(character)
            if not observed.is_set():
                observed.set()
                if not release.wait(10):
                    raise AssertionError('Sincronização expirou.')
            return result

        def approve():
            try:
                return self.request(self.master, 'post', f'/api/submissions/{submission}/reviews', {'status': 'approved'})
            finally:
                connections.close_all()

        def decide():
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pids['decision'] = cursor.fetchone()[0]
                ready.set()
                return self.request(self.master, 'post', f'/api/campaigns/{self.campaign.pk}/decisions',
                                    {'ruleId': 'R08', 'value': {'eligibility': 'Nova decisão sintética'}, 'reason': 'Teste.'})
            finally:
                connections.close_all()

        with patch('core.views.decisions_for', side_effect=held_decisions), ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(approve)
            try:
                self.assertTrue(observed.wait(8))
                second = pool.submit(decide)
                self.assertTrue(ready.wait(8))
                self.wait_for_lock(pids['decision'])
            finally:
                release.set()
            approved, decided = first.result(timeout=20), second.result(timeout=20)
        self.assertEqual(approved.status_code, 200)
        self.assertTrue(approved.data['approved'])
        self.assertEqual(decided.status_code, 201)
        self.assertFalse(self.request(self.master, 'get', self.url, {}).data['approved'])
        self.assertEqual(Review.objects.get().status, 'approved')

    def test_global_decision_first_rejects_approval_after_real_lock(self):
        self.resolve()
        submission = self.submit()
        ready = Event()
        pids = {}

        def approve():
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pids['review'] = cursor.fetchone()[0]
                ready.set()
                return self.request(self.master, 'post', f'/api/submissions/{submission}/reviews', {'status': 'approved'})
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Campaign.objects.select_for_update().get(pk=self.campaign.pk)
                response = self.request(self.master, 'post', f'/api/campaigns/{self.campaign.pk}/decisions',
                                        {'ruleId': 'R08', 'value': {'eligibility': 'Mudou'}, 'reason': 'Teste.'})
                self.assertEqual(response.status_code, 201)
                future = pool.submit(approve)
                self.assertTrue(ready.wait(8))
                self.wait_for_lock(pids['review'])
            result = future.result(timeout=20)
        self.assertEqual(result.status_code, 409)
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.filter(action='review.approved').count(), 0)
