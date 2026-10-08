import secrets
import uuid
from django.conf import settings
from django.db import models


def invite_token():
    return secrets.token_urlsafe(32)


class RulesetVersion(models.Model):
    label = models.CharField(max_length=120, default='Word • nível 1 • em validação')
    source_hash = models.CharField(max_length=64)
    catalog = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        if self.pk and RulesetVersion.objects.filter(pk=self.pk).exists():
            raise ValueError('Versão das regras é imutável. Crie uma nova versão.')
        return super().save(*args, **kwargs)


class Campaign(models.Model):
    name = models.CharField(max_length=120)
    master = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    ruleset = models.ForeignKey(RulesetVersion, on_delete=models.PROTECT)


class Membership(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['campaign', 'user'], name='unique_membership')]


class Invite(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=invite_token)
    expires_at = models.DateTimeField()
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    consumed = models.BooleanField(default=False)


class RuleDecision(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    rule_id = models.CharField(max_length=32)
    value = models.JSONField()
    reason = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    character = models.ForeignKey('Character', null=True, blank=True, on_delete=models.CASCADE)
    applies_revision = models.PositiveIntegerField(null=True)


class Character(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT)
    ruleset = models.ForeignKey(RulesetVersion, on_delete=models.PROTECT)
    data = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=1)
    resources = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)


class Submission(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='submissions')
    revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    report = models.JSONField()
    decisions = models.JSONField(default=list)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['character', 'revision'], name='unique_submission_revision')]


class Review(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=[('approved', 'Aprovada'), ('changes', 'Ajustes solicitados')])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Asset(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    label = models.CharField(max_length=120)
    file = models.FileField(upload_to='tokens/')
    approved = models.BooleanField(default=False)
    sha256 = models.CharField(max_length=64)


class AuditEvent(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    entity = models.CharField(max_length=80)
    revision = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
