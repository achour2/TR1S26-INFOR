import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django import forms
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import CodeVerification
from travelhub.models import Activite, destinations, voyages


def _hash_code(token, code):
    return salted_hmac("compte.code-verification", f"{token}:{code}", secret=settings.SECRET_KEY).hexdigest()


def _envoyer_code(user, purpose, email, payload=None):
    if not email:
        raise ValueError("Aucune adresse courriel n'est associée à ce compte.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    verification = CodeVerification.objects.create(
        user=user,
        purpose=purpose,
        email=email,
        payload=payload or {},
        expires_at=timezone.now() + timedelta(minutes=settings.ACCOUNT_VERIFICATION_CODE_TTL_MINUTES),
        code_hash="pending",
    )
    verification.code_hash = _hash_code(verification.token, code)
    verification.save(update_fields=("code_hash",))
    action = verification.get_purpose_display().lower()
    try:
        send_mail(
            subject=f"Votre code TravelHub — {action}",
            message=(
                f"Bonjour {user.username},\n\nVotre code de vérification est : {code}\n"
                f"Il expire dans {settings.ACCOUNT_VERIFICATION_CODE_TTL_MINUTES} minutes.\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        verification.delete()
        raise
    CodeVerification.objects.filter(user=user, purpose=purpose).exclude(pk=verification.pk).delete()
    return verification


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(label="Adresse courriel", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class ProfilForm(forms.ModelForm):
    email = forms.EmailField(label="Adresse courriel", required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Prénom", "last_name": "Nom", "email": "Adresse courriel"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse courriel est déjà utilisée.")
        return email


class SuppressionCompteForm(forms.Form):
    password = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Le mot de passe est incorrect.")
        return password


def inscription(request):
    if request.user.is_authenticated:
        return redirect("voyage:liste_voyages")

    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        utilisateur.is_active = False
        utilisateur.save(update_fields=("is_active",))
        try:
            verification = _envoyer_code(
                utilisateur, CodeVerification.Purpose.ACTIVER, utilisateur.email
            )
        except Exception:
            utilisateur.delete()
            form.add_error(None, "Le courriel n'a pas pu être envoyé. Vérifiez la configuration du serveur mail et réessayez.")
        else:
            return redirect("compte:verifier_code", token=verification.token)

    return render(request, "compte/inscription.html", {"form": form})


@login_required
def profil(request):
    return render(request, "compte/profil.html", {
        "nombre_voyages": voyages.objects.filter(utilisateurs=request.user).count(),
        "nombre_destinations": destinations.objects.filter(voyages__utilisateurs=request.user).distinct().count(),
        "nombre_activites": Activite.objects.filter(
            destination__voyages__utilisateurs=request.user
        ).distinct().count(),
    })


@login_required
def modifier_profil(request):
    form = ProfilForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        changements = form.cleaned_data
        try:
            verification = _envoyer_code(
                request.user,
                CodeVerification.Purpose.PROFIL,
                changements["email"],
                {
                    "first_name": changements["first_name"],
                    "last_name": changements["last_name"],
                    "email": changements["email"],
                },
            )
        except Exception:
            form.add_error(None, "Le courriel de vérification n'a pas pu être envoyé. Aucune modification n'a été appliquée.")
        else:
            return redirect("compte:verifier_code", token=verification.token)
    return render(request, "compte/modifier_profil.html", {"form": form})


@login_required
def modifier_mot_de_passe(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            verification = _envoyer_code(
                request.user,
                CodeVerification.Purpose.MOT_DE_PASSE,
                request.user.email,
                {"password_hash": make_password(form.cleaned_data["new_password1"])},
            )
        except Exception:
            form.add_error(None, "Le courriel de vérification n'a pas pu être envoyé. Le mot de passe n'a pas été modifié.")
        else:
            return redirect("compte:verifier_code", token=verification.token)
    return render(request, "compte/modifier_mot_de_passe.html", {"form": form})


@login_required
def supprimer_compte(request):
    form = SuppressionCompteForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            verification = _envoyer_code(
                request.user, CodeVerification.Purpose.SUPPRIMER, request.user.email
            )
        except Exception:
            form.add_error(None, "Le courriel de vérification n'a pas pu être envoyé. Le compte n'a pas été supprimé.")
        else:
            return redirect("compte:verifier_code", token=verification.token)
    return render(request, "compte/supprimer_compte.html", {"form": form})


@transaction.atomic
def verifier_code(request, token):
    verification = get_object_or_404(CodeVerification, token=token)
    if verification.purpose != CodeVerification.Purpose.ACTIVER:
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.pk != verification.user_id:
            raise Http404

    form = CodeVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if verification.expired:
            verification.delete()
            form.add_error(None, "Ce code a expiré. Recommencez l'opération pour recevoir un nouveau code.")
        elif not secrets.compare_digest(
            verification.code_hash,
            _hash_code(verification.token, form.cleaned_data["code"]),
        ):
            verification.attempts += 1
            if verification.attempts >= 5:
                verification.delete()
                form.add_error(None, "Trop de tentatives. Recommencez l'opération pour recevoir un nouveau code.")
            else:
                verification.save(update_fields=("attempts",))
                form.add_error("code", "Le code est incorrect.")
        else:
            utilisateur = verification.user
            purpose = verification.purpose
            payload = verification.payload
            verification.delete()
            if purpose == CodeVerification.Purpose.ACTIVER:
                utilisateur.is_active = True
                utilisateur.save(update_fields=("is_active",))
                return redirect("login")
            if purpose == CodeVerification.Purpose.PROFIL:
                for field in ("first_name", "last_name", "email"):
                    setattr(utilisateur, field, payload[field])
                utilisateur.save(update_fields=("first_name", "last_name", "email"))
                return redirect("compte:profil")
            if purpose == CodeVerification.Purpose.MOT_DE_PASSE:
                utilisateur.password = payload["password_hash"]
                utilisateur.save(update_fields=("password",))
                update_session_auth_hash(request, utilisateur)
                return redirect("compte:profil")
            if purpose == CodeVerification.Purpose.SUPPRIMER:
                logout(request)
                utilisateur.delete()
                return redirect("login")
    return render(request, "compte/verifier_code.html", {
        "form": form,
        "verification": verification,
    })


def renvoyer_code(request, token):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    verification = get_object_or_404(CodeVerification, token=token)
    if verification.purpose != CodeVerification.Purpose.ACTIVER:
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.pk != verification.user_id:
            raise Http404
    try:
        nouveau_code = _envoyer_code(
            verification.user,
            verification.purpose,
            verification.email,
            verification.payload,
        )
    except Exception:
        form = CodeVerificationForm()
        form.add_error(None, "Le courriel n'a pas pu être envoyé. Vous pouvez réessayer.")
        return render(request, "compte/verifier_code.html", {
            "form": form,
            "verification": verification,
        })
    return redirect("compte:verifier_code", token=nouveau_code.token)


class CodeVerificationForm(forms.Form):
    code = forms.RegexField(
        regex=r"^\d{6}$",
        label="Code à 6 chiffres",
        error_messages={"invalid": "Saisissez les 6 chiffres reçus par courriel."},
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code", "maxlength": "6"}),
    )
