from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# class utilisateurs (models.Model):
#     nom = models.CharField(max_length=100)
#     prenom = models.CharField(max_length=100)
#     email = models.EmailField( max_length=100) # EmailField : vérifie  que le format d'un email est valide
#     proprietaire=models.BooleanField(default=False)
    # est ce que on doit ajouter un mot de passe ??



# class Profile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE
#     )
        
class   voyages (models.Model):
    class Statut(models.TextChoices): #les etats possibles pour le statut
            PLANIFIE = 'planifie', 'Planifié'
            EN_COURS = 'en_cours', 'En cours'
            TERMINE = 'termine', 'Terminé'
            ANNULE = 'annule', 'Annulé'
    titre = models.CharField(  max_length=100)
    description =models.CharField( max_length=1000)
    date_Debut = models.DateField(default=timezone.now) # une fonction qui permet de entrer une dete AAAA-MM-JJ
    date_Fin = models.DateField (default=timezone.now)
    status = models.CharField(  max_length=20,choices=Statut.choices,default=Statut.PLANIFIE) # il est obligatoire de choisir un etat parmi ce qu'on a
    createur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voyages_crees",
        verbose_name="créateur",
    )
    utilisateurs = models.ManyToManyField(
        User,
        related_name="voyages_participes",
        verbose_name="participants",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_Debut__lte=models.F("date_Fin")),
                name="voyage_dates_coherentes",
            ),
        ]
    

class destinations(models.Model):
    ville=models.CharField(max_length=100)
    pays=models.CharField(max_length=500)
    date_Arrive = models.DateField(default=timezone.now) # une fonction qui permet de entrer une dete AAAA-MM-JJ
    date_Depart = models.DateField (default=timezone.now)
    voyages = models.ForeignKey(voyages, on_delete=models.CASCADE, related_name="destinations")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_Arrive__lte=models.F("date_Depart")),
                name="destination_dates_coherentes",
            ),
        ]

class Activite(models.Model):
    nom = models.CharField(  max_length=100)
    description =models.CharField( max_length=1000)
    categorie=models.CharField( max_length=1000)
    date = models.DateField(default=timezone.now) # une fonction qui permet de entrer une dete AAAA-MM-JJ
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    destination = models.ForeignKey(destinations, on_delete=models.CASCADE, related_name="activites")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cout__gte=0),
                name="activite_cout_non_negatif",
            ),
        ]
   
