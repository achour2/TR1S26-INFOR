import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class CodeVerification(models.Model):
    class Purpose(models.TextChoices):
        ACTIVER = "activate", "Activation du compte"
        PROFIL = "profile", "Modification du profil"
        MOT_DE_PASSE = "password", "Modification du mot de passe"
        SUPPRIMER = "delete", "Suppression du compte"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codes_verification",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    purpose = models.CharField(max_length=12, choices=Purpose.choices)
    email = models.EmailField()
    code_hash = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=("user", "purpose"))]

    @property
    def expired(self):
        return timezone.now() >= self.expires_at

# Create your models here.
