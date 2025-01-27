from users.models import CustomUser


def check_user_in_created_or_shared(
        created_by: CustomUser = None,
        shared_with=None,
        user: CustomUser = None,
        same_email_users=None,
        ) -> bool:
    if created_by:
        same_email_users = CustomUser.objects.filter(email=created_by.email)
    if same_email_users and user in same_email_users:
        return True
    if shared_with and user.email in [user.email for user in shared_with]:
        return True
    return False
