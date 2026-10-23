from django.urls import path,include

import voyage
from . import views

app_name = 'voyage'

urlpatterns = [


    path('', views.creer_voyage, name='creer'),
    path ('', views.liste_voyages, name='liste_voyages'),
]