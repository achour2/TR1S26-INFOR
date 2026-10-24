from django.urls import path

from . import views

app_name = "destination"

urlpatterns = [
    path("", views.creer_destination, name="creer"),
    path("<int:destination_pk>/", views.detail_destination, name="detail"),
    path("<int:destination_pk>/modifier/", views.modifier_destination, name="modifier"),
    path("<int:destination_pk>/supprimer/", views.supprimer_destination, name="supprimer"),
]
