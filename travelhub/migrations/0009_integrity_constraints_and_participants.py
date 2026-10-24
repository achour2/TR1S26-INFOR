from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("travelhub", "0008_destination_activity_relations"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="voyages",
            name="utilisateurs",
            field=models.ManyToManyField(
                related_name="voyages_participes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="participants",
            ),
        ),
        migrations.AddConstraint(
            model_name="voyages",
            constraint=models.CheckConstraint(
                condition=models.Q(date_Debut__lte=models.F("date_Fin")),
                name="voyage_dates_coherentes",
            ),
        ),
        migrations.AddConstraint(
            model_name="destinations",
            constraint=models.CheckConstraint(
                condition=models.Q(date_Arrive__lte=models.F("date_Depart")),
                name="destination_dates_coherentes",
            ),
        ),
        migrations.AddConstraint(
            model_name="activite",
            constraint=models.CheckConstraint(
                condition=models.Q(cout__gte=0),
                name="activite_cout_non_negatif",
            ),
        ),
    ]
