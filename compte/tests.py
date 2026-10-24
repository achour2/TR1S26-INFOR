import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountVerificationTests(TestCase):
    password = "Long-test-pass_38!"

    def verification_url_and_code(self, response):
        self.assertEqual(response.status_code, 302)
        token = response.url.rstrip("/").split("/")[-1]
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        return reverse("compte:verifier_code", kwargs={"token": token}), code

    def test_registration_requires_email_code_before_login(self):
        response = self.client.post(reverse("compte:inscription"), {
            "username": "nouveau", "email": "nouveau@example.com",
            "password1": self.password, "password2": self.password,
        })
        user = User.objects.get(username="nouveau")
        self.assertFalse(user.is_active)
        self.assertEqual(mail.outbox[-1].to, [user.email])
        verify_url, code = self.verification_url_and_code(response)
        verified = self.client.post(verify_url, {"code": code})
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertRedirects(verified, reverse("login"), fetch_redirect_response=False)

    def test_profile_changes_apply_only_after_code_confirmation(self):
        user = User.objects.create_user("profil", email="old@example.com", password=self.password)
        self.client.force_login(user)
        response = self.client.post(reverse("compte:modifier_profil"), {
            "first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com",
        })
        user.refresh_from_db()
        self.assertEqual(user.email, "old@example.com")
        verify_url, code = self.verification_url_and_code(response)
        self.client.post(verify_url, {"code": code})
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name, user.email), ("Ada", "Lovelace", "ada@example.com"))

    def test_password_change_requires_code_and_keeps_session(self):
        user = User.objects.create_user("motdepasse", email="password@example.com", password=self.password)
        self.client.force_login(user)
        new_password = "Another-long-pass_93!"
        response = self.client.post(reverse("compte:modifier_mot_de_passe"), {
            "old_password": self.password,
            "new_password1": new_password,
            "new_password2": new_password,
        })
        self.assertTrue(user.check_password(self.password))
        verify_url, code = self.verification_url_and_code(response)
        verified = self.client.post(verify_url, {"code": code})
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertEqual(verified.status_code, 302)
        self.assertTrue(self.client.get(reverse("compte:profil")).wsgi_request.user.is_authenticated)

    def test_deletion_requires_password_and_email_code(self):
        user = User.objects.create_user("effacer", email="delete@example.com", password=self.password)
        self.client.force_login(user)
        response = self.client.post(reverse("compte:supprimer_compte"), {"password": self.password})
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        verify_url, code = self.verification_url_and_code(response)
        verified = self.client.post(verify_url, {"code": code})
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertRedirects(verified, reverse("login"), fetch_redirect_response=False)

    def test_wrong_code_does_not_apply_change(self):
        user = User.objects.create_user("incorrect", email="incorrect@example.com", password=self.password)
        self.client.force_login(user)
        response = self.client.post(reverse("compte:modifier_profil"), {
            "first_name": "Non", "last_name": "Confirmé", "email": "new@example.com",
        })
        verify_url, valid_code = self.verification_url_and_code(response)
        wrong_code = f"{(int(valid_code) + 1) % 1_000_000:06d}"
        invalid = self.client.post(verify_url, {"code": wrong_code})
        user.refresh_from_db()
        self.assertEqual(user.email, "incorrect@example.com")
        self.assertEqual(invalid.status_code, 200)

    def test_expired_or_lost_code_can_be_resent(self):
        response = self.client.post(reverse("compte:inscription"), {
            "username": "renvoi", "email": "renvoi@example.com",
            "password1": self.password, "password2": self.password,
        })
        verify_url, _ = self.verification_url_and_code(response)
        token = verify_url.rstrip("/").split("/")[-1]
        resend = self.client.post(reverse("compte:renvoyer_code", kwargs={"token": token}))
        new_verify_url, new_code = self.verification_url_and_code(resend)
        self.assertNotEqual(verify_url, new_verify_url)
        verified = self.client.post(new_verify_url, {"code": new_code})
        self.assertRedirects(verified, reverse("login"), fetch_redirect_response=False)
