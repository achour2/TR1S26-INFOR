from django.urls import path

from . import views

app_name = "compte"

urlpatterns = [
    path("", views.profil, name="profil"),
    path("inscription/", views.inscription, name="inscription"),
    path("modifier/", views.modifier_profil, name="modifier_profil"),
    path("mot-de-passe/", views.modifier_mot_de_passe, name="modifier_mot_de_passe"),
    path("supprimer/", views.supprimer_compte, name="supprimer_compte"),
    path("verifier/<uuid:token>/", views.verifier_code, name="verifier_code"),
    path("verifier/<uuid:token>/renvoyer/", views.renvoyer_code, name="renvoyer_code"),
]
