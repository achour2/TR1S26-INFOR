from django.contrib.auth.models import User
from django.db import models


class utilisateurs (models.Model):
    nom = models.CharField('Nom', max_length=100)
    prenom = models.CharField('Prenom', max_length=100)
    email = models.EmailField('Email', max_length=100) # EmailField : vérifie  que le format d'un email est valide
    # est ce que on doit ajouter un mot de passe ??
