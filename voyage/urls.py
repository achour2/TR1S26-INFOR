from django.urls import include, path

from . import views

app_name = "voyage"

urlpatterns = [
    path("", views.liste_voyages, name="liste_voyages"),
    path("creer/", views.creer_voyage, name="creer"),
    path("<int:pk>/", views.detail_voyage, name="detail"),
    path("<int:pk>/modifier/", views.modifier_voyage, name="modifier"),
    path("<int:pk>/supprimer/", views.supprimer_voyage, name="supprimer"),
    path("<int:voyage_pk>/destinations/", include("destination.urls")),
]
