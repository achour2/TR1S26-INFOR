from django.urls import include, path

from . import views
from destination import views as destination_views

urlpatterns = [
    path("", views.accueil, name="travelhub_accueil"),
    path("voyage/", include("voyage.urls")),
    path("destinations/", destination_views.liste_destinations, name="travelhub_destinations"),
    path("activites/", include("activite.urls")),
    path("compte/", include("compte.urls")),
]
