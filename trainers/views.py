from django.http import QueryDict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from trainers.models import (
    Trainer,
    WorkHours,
)
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
    SearchVector,
)
from django.db.models import Q
from trainers.serializers import (
    TrainerSerializer,
    TrainerGetSerializer,
    WorkHoursSerializer,
    WeekDaySerializer,
)
from trainers.models import WeekDay


class TrainerView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class TrainerSearchView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        if pk:
            trainer = get_object_or_404(Trainer, pk=pk)
            trainer_of_user = trainer.clients_of_trainer
            serializer = TrainerGetSerializer(trainer)
            if request.user.is_authenticated and request.user.trainer == trainer:
                return Response(serializer.data, status=status.HTTP_200_OK)
            if trainer.is_active:
                if trainer.is_public:
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    if request.user.is_authenticated and trainer_of_user.found_by_link:
                        return Response(
                            serializer.data,
                            status=status.HTTP_200_OK
                        )
                    else:
                        return Response({'message': 'Trainer is not public'},
                                        status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {'message': 'Trainer is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Получаем строку поиска
        search_query = request.query_params.get('search', '')
        if not search_query:
            return Response({'trainers': []})  # Пустой запрос

        # Разделяем строку поиска на слова
        tokens = search_query.split()

        # Массив для фильтров
        filters = Q()
        trigram_scores = []

        for token in tokens:
            # Генерация фильтров
            filters |= Q(user__first_name__trigram_similar=token)
            filters |= Q(user__last_name__trigram_similar=token)
            filters |= Q(description__trigram_similar=token)
            filters |= Q(is_public=True)

            # Триграммные ранги для сортировки
            trigram_scores.append(
                TrigramSimilarity('user__first_name', token) +
                TrigramSimilarity('user__last_name', token) +
                TrigramSimilarity('description', token)
            )

        # Общий trigram_score для сортировки
        combined_trigram_score = sum(trigram_scores)

        # Полнотекстовый запрос
        search_vector = SearchVector('user__first_name',
                                     'user__last_name',
                                     'description')
        search_query = SearchQuery(search_query, search_type='plain')

        # Выполняем поиск
        trainers = Trainer.objects.annotate(
            # Ранг полнотекстового поиска
            rank=SearchRank('search_vector', search_vector),
            trigram_score=combined_trigram_score  # Итоговый триграммный ранг
        ).filter(
            filters
        ).order_by(
            '-rank',  # Сначала по полнотекстовому рангу
            '-trigram_score'  # Затем по триграммной схожести
        )
        serializer_trainers = TrainerGetSerializer(trainers, many=True)

        return Response(serializer_trainers.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        trainer = get_object_or_404(Trainer, pk=pk)
        if request.user.trainer != trainer:
            return Response(
                {'message': 'You are not authorized to edit this trainer.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = TrainerSerializer(
            trainer, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Trainer updated successfully'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkHoursGetPutView(APIView):
    http_method_names = ['get', 'put']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request, trainer_id):
        trainer = get_object_or_404(Trainer, pk=trainer_id)
        trainer_of_user = trainer.clients_of_trainer

        work_hours = get_object_or_404(WorkHours, trainer=trainer)
        serializer = WorkHoursSerializer(work_hours)

        if request.user.is_authenticated and request.user.trainer == trainer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        if trainer.is_active:
            if trainer.is_public:
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                if (request.user.is_authenticated
                   and trainer_of_user.found_by_link):
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Trainer is not public'},
                                    status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Trainer is not active'},
                        status=status.HTTP_400_BAD_REQUEST)

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
