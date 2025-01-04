from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import BaseUserManager
from trainers.models import Trainer
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
)


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
            serializer = TrainerGetSerializer(trainer)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Trainer updated successfully'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkHoursView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        if request.user.trainer.id == request.data['trainer']:
            serializer = WorkHoursSerializer(data=request.data,
                                             context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'User created successfully'},
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)