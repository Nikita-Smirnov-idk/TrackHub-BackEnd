# Generated by Django 5.1.4 on 2025-03-08 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_alter_customuser_first_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="review",
            name="review_text",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
