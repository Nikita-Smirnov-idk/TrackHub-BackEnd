# Generated by Django 5.1.4 on 2025-02-10 07:50

import django.contrib.postgres.indexes
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainers", "0044_remove_experience_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="trainer",
            name="trainers_tr_descrip_39229f_gin",
        ),
        migrations.AddIndex(
            model_name="trainer",
            index=django.contrib.postgres.indexes.GinIndex(
                django.contrib.postgres.indexes.OpClass(
                    django.db.models.functions.text.Lower("description"),
                    name="gin_trgm_ops",
                ),
                name="description_gin_trgm_idx",
            ),
        ),
    ]
