from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from trainers.models import (
    Trainer,
    WorkHours,
    Experience,
    WholeExperience,
    Gym,
)
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
    SearchVector,
)
from trainers.serializers import (
    TrainerSerializer,
    TrainerGetSerializer,
    WorkHoursSerializer,
    ExperienceSerializer,
    WholeExperienceSerializer,
    GymSerializer,
)
from trainers.permissions import (
    IsTrainer,
    IsClient,
    choose_what_to_return_for_trainer
)
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat


class TrainerDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['get']

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated(), IsTrainer()]
    
    def get(self, request, trainer_id):
        is_client_permission = IsClient()

        experience = get_object_or_404(Experience, pk=trainer_id)
        trainer = get_object_or_404(Trainer, pk=experience.trainer.id)

        if is_client_permission.has_permission(request, self):
            trainer_of_user = trainer.clients_of_trainer.filter(
                client=request.user.client
            ).first()
        else:
            trainer_of_user = None

        serializer = TrainerGetSerializer(experience)
        data = serializer.data
        return choose_what_to_return_for_trainer(
            self,
            request,
            trainer,
            data,
            trainer_of_user
        )

class TrainerChangeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['put']

    def get_permissions(self):
        return [IsAuthenticated(), IsTrainer()]
    
    def put(self, request):
        user = request.user
        trainer = get_object_or_404(Trainer, pk=user.trainer.id)

        serializer = TrainerSerializer(
            trainer, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Trainer updated successfully'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        


class TrainerSearchView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    
    def get(self, request):
        # Получаем строку поиска
        query = request.query_params.get('search', '')
        if not query:
            return Response({'trainers': []})  # Пустой запрос

        # Разделяем запрос на слова
        words = query.split()

        # Создаем условия для триграммного поиска
        trigram_conditions = Q()
        for word in words:
            trigram_conditions |= (
                Q(user__first_name__trigram_similar=word) |
                Q(user__last_name__trigram_similar=word) |
                Q(description__icontains=word) |
                Q(description__trigram_similar=word)
            )

        # Создаем условия для полнотекстового поиска
        search_vector = (
            SearchVector('user__first_name', weight='A') +
            SearchVector('user__last_name', weight='A') +
            SearchVector('description', weight='B')
        )
        search_query = SearchQuery(query, search_type='plain')
        search_rank = SearchRank(search_vector, search_query)

        # Ищем тренеров, соответствующих условиям
        trainers = Trainer.objects.annotate(
            full_name=Concat(
                'user__first_name', Value(' '), 'user__last_name',
                output_field=CharField()
            ),
            similarity=(
                TrigramSimilarity('user__first_name', query) +
                TrigramSimilarity('user__last_name', query) +
                TrigramSimilarity('description', query) +
                TrigramSimilarity('full_name', query)
            ),
            rank=search_rank
        ).filter(trigram_conditions).order_by('-rank', '-similarity')

        serializer_trainers = TrainerGetSerializer(trainers, many=True)

        return Response(serializer_trainers.data, status=status.HTTP_200_OK)


class WorkHoursGetPutView(APIView):
    http_method_names = ['get', 'put']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated(), IsTrainer()]

    def get(self, request, trainer_id):
        is_client_permission = IsClient()

        trainer = get_object_or_404(Trainer, pk=trainer_id)

        if is_client_permission.has_permission(request, self):
            trainer_of_user = trainer.clients_of_trainer.get(
                client=request.user.client
            )
        else:
            trainer_of_user = None

        work_hours = get_object_or_404(WorkHours, trainer=trainer)
        serializer = WorkHoursSerializer(work_hours)
        data = serializer.data
        return choose_what_to_return_for_trainer(
            self,
            request,
            trainer,
            data,
            trainer_of_user
        )

    def put(self, request, trainer_id):
        if 'trainer_id' in request.data:
            return Response(
                {'message': 'You can not have trainer in ' +
                 'request data. You already have it in url.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        trainer = get_object_or_404(Trainer, pk=trainer_id)
        if request.user.trainer != trainer:
            return Response(
                {'message': 'You are not authorized to edit this trainer.'},
                status=status.HTTP_403_FORBIDDEN
            )
        work_hours = get_object_or_404(WorkHours, trainer=trainer)
        serializer = WorkHoursSerializer(
            work_hours, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExperienceDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated(), IsTrainer()]

    def get(self, request, experience_id):
        is_client_permission = IsClient()

        experience = get_object_or_404(Experience, pk=experience_id)
        trainer = get_object_or_404(Trainer, pk=experience.trainer.id)

        if is_client_permission.has_permission(request, self):
            trainer_of_user = trainer.clients_of_trainer.filter(
                client=request.user.client
            ).first()
        else:
            trainer_of_user = None

        serializer = ExperienceSerializer(experience)
        data = serializer.data
        return choose_what_to_return_for_trainer(
            self,
            request,
            trainer,
            data,
            trainer_of_user
        )

    def put(self, request, experience_id):
        if 'trainer_id' in request.data:
            return Response(
                {'message': 'You can not have trainer in ' +
                 'request data. You already have it in url.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        experience = get_object_or_404(Experience, pk=experience_id)
        trainer = get_object_or_404(Trainer, pk=experience.trainer.id)

        if request.user.trainer != trainer:
            return Response(
                {'message': 'You are not authorized to edit this trainer.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ExperienceSerializer(
            experience, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, experience_id):
        experience = get_object_or_404(Experience, pk=experience_id)
        trainer = get_object_or_404(Trainer, pk=experience.trainer.id)
        if request.user.trainer != trainer:
            return Response(
                {'message': 'You are not authorized to edit this trainer.'},
                status=status.HTTP_403_FORBIDDEN
            )
        experience.delete()
        return Response(
            {'message': 'Experience deleted successfully'},
            status=status.HTTP_200_OK
        )


class ExperiencesOfTrainerView(APIView):
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]

    def get(self, request, trainer_id):
        is_client_permission = IsClient()

        trainer = get_object_or_404(Trainer, pk=trainer_id)

        if is_client_permission.has_permission(request, self):
            trainer_of_user = trainer.clients_of_trainer.get(
                client=request.user.client
            )
        else:
            trainer_of_user = None

        data = []

        experiences = Experience.objects.filter(trainer=trainer)
        whole_experience = WholeExperience.objects.get(trainer=trainer)

        data.append(WholeExperienceSerializer(whole_experience).data)

        for experience in experiences:
            serializer = ExperienceSerializer(experience)
            data.append(serializer.data)

        return choose_what_to_return_for_trainer(
            self,
            request,
            trainer,
            data,
            trainer_of_user
        )


class ExperienceView(APIView):
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [IsAuthenticated(), IsTrainer()]

    def post(self, request):
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["trainer"] = request.user.trainer.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        serializer = ExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GymCreateView(APIView):
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [IsAuthenticated(), IsTrainer()]
    
    def post(self, request):
        serializer = GymSerializer(data=request.data)
        if serializer.is_valid():
            gym = serializer.save(trainer=request.user.trainer)
            return Response({
                'message': 'Gym created successfully!',
                'gym_id': gym.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GymChangeView(APIView):
    http_method_names = ['delete', 'put']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [IsAuthenticated(), IsTrainer()]
    
    def delete(self, request, gymId):
        gym = get_object_or_404(Gym, pk=gymId)
        if gym.trainer == request.user.trainer:
            gym.delete()
        
        else:
            return Response(
                {'message': 'You are not authorized to delete this gym.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(
            {'message': 'Gym deleted successfully'},
            status=status.HTTP_200_OK
        )
    
    def put(self, request, gymId):

        gym = get_object_or_404(Gym, pk=gymId)

        if request.user.trainer != gym.trainer:
            return Response(
                {'message': 'You are not authorized to edit this trainer.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = GymSerializer(
            gym, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(trainer=request.user.trainer)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)