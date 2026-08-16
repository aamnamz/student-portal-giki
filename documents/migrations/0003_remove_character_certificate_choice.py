from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_alter_document_doc_type")]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="doc_type",
            field=models.CharField(choices=[("cnic_bform", "CNIC Copy"), ("father_cnic", "Father's CNIC Copy"), ("matric_certificate", "Matric Certificate"), ("intermediate_certificate", "Intermediate Certificate"), ("domicile_certificate", "Domicile Certificate")], max_length=30),
        ),
    ]
