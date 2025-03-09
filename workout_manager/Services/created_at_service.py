from django.utils.timezone import now


def update_changed_at(instance, old_instance):
    if old_instance:
        field_names = [field.name for field in instance._meta.fields]
        changed_fields = [
            field for field in field_names
            if getattr(old_instance, field) != getattr(instance, field)
        ]
        if changed_fields:
            instance.changed_at = now()