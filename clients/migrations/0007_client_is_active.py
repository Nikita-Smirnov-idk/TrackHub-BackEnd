# Generated by Django 5.1.4 on 2025-01-14 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0006_alter_client_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]
