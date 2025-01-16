from rest_framework.permissions import BasePermission


class IsTrainer(BasePermission):
    """
    Custom permission to check if the user is a trainer.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and has a related Trainer profile
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_trainer
            and hasattr(request.user, 'trainer')
        )
