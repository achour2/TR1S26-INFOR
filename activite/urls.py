from django.urls import path

from . import views

app_name = "activite"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("<int:voyage_pk>/<int:destination_pk>/creer/", views.creer, name="creer"),
    path("<int:voyage_pk>/<int:destination_pk>/<int:activite_pk>/modifier/", views.modifier, name="modifier"),
    path("<int:voyage_pk>/<int:destination_pk>/<int:activite_pk>/supprimer/", views.supprimer, name="supprimer"),
]
