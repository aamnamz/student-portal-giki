from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("applications", "0006_alter_application_cnic_or_bform")]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="matric_board",
            field=models.CharField(blank=True, max_length=150, verbose_name="Matric Group"),
        ),
        migrations.AddField(
            model_name="application",
            name="intermediate_result",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
