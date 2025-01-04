from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trainers", "0018_trainer_trainers_tr_descrip_39229f_gin"),
    ]

    operations = [
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    ]