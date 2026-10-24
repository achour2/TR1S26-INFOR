from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("travelhub", "0007_alter_voyages_titre")]

    operations = [
        migrations.AlterField(
            model_name="destinations",
            name="voyages",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="destinations",
                to="travelhub.voyages",
            ),
        ),
        migrations.AlterField(
            model_name="activite",
            name="destination",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="activites",
                to="travelhub.destinations",
            ),
        ),
        migrations.AlterField(
            model_name="activite",
            name="cout",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
