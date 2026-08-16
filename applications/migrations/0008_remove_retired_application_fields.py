from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("applications", "0007_application_intermediate_result_and_matric_group")]

    operations = [
        migrations.RemoveField(model_name="application", name="whatsapp"),
        migrations.RemoveField(model_name="application", name="previous_qualification"),
        migrations.RemoveField(model_name="application", name="previous_institution"),
        migrations.RemoveField(model_name="application", name="previous_year"),
        migrations.RemoveField(model_name="application", name="previous_cgpa"),
    ]
