from django.contrib.auth.models import User
from django.db import models


class utilisateurs (models.Model):
    nom = models.CharField('Nom', max_length=100)
    prenom = models.CharField('Prenom', max_length=100)
    email = models.EmailField('Email', max_length=100) # EmailField : vérifie  que le format d'un email est valide
    # est ce que on doit ajouter un mot de passe ??


class   voyages (models.Model):
    class Statut(models.TextChoices): #les etats possibles pour le statut
        PLANIFIE = 'planifie', 'Planifié'
        EN_COURS = 'en_cours', 'En cours'
        TERMINE = 'termine', 'Terminé'
        ANNULE = 'annule', 'Annulé'
    titre = models.CharField( 'titre', max_length=100)
    description =models.CharField( 'description', max_length=1000)
    dateD = models.DateField('dates de début') # une fonction qui permet de entrer une dete AAAA-MM-JJ
    dateF = models.DateField ('date de fin')
    #
    statut = models.CharField('statut',
                              max_length=20,
                              choices=Statut.choices,
                              default=Statut.PLANIFIE,
                              ) # il est obligatoire de choisir un etat parmi ce qu'on a