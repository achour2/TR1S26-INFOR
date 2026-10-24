from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("travelhub", "0009_integrity_constraints_and_participants"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="voyages",
            name="createur",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="voyages_crees",
                to=settings.AUTH_USER_MODEL,
                verbose_name="créateur",
            ),
        ),
    ]
