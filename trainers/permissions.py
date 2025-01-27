from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status


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


class IsClient(BasePermission):
    """
    Custom permission to check if the user is a trainer.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and has a related Trainer profile
        return (
            request.user
            and request.user.is_authenticated
            and not request.user.is_trainer
            and hasattr(request.user, 'client')
        )


def choose_what_to_return_for_trainer(
        self,
        request,
        trainer,
        data,
        trainer_of_user
):
    is_trainer_permission = IsTrainer()

    if (
            is_trainer_permission.has_permission(request, self) and
            request.user.trainer == trainer
    ):
        return Response(data, status=status.HTTP_200_OK)
    if trainer.is_active:
        if trainer.is_public:
            return Response(data, status=status.HTTP_200_OK)
        else:
            if (
                trainer_of_user and
                trainer_of_user.found_by_link
            ):
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Trainer is not public'},
                                status=status.HTTP_403_FORBIDDEN)
    return Response({'message': 'Trainer is not active'},
                    status=status.HTTP_400_BAD_REQUEST)
