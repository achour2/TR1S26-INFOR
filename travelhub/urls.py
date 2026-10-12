from django.urls import path
from . import views

urlpatterns = [
    path("", views.reponse,name="reponse"),
]