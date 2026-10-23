from django.urls import path,include

from voyage import views
from . import views

urlpatterns = [
    path("", views.reponse,name="reponse"),
    path("voyage/", include("voyage.urls")),

]