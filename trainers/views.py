from django.http import QueryDict
from rest_framework.views import APIView
from rest_framework.response import Response
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
    ExerciseSerializer,
    WorkoutSerializer,
    WorkoutExerciseSerializer
)
from trainers.models import (
    Exercise,
    Workout,
    WorkoutExercise,
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


class ExerciseView(APIView):
    http_method_names = ['get', 'post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request):
        exercises = []

        for exercise in Exercise.objects.filter(is_public=True):
            exercises.append(ExerciseSerializer(exercise).data)

        if request.user.is_authenticated:
            created_by_exercises = Exercise.objects.filter(
                created_by=request.user
            )
            for exercise in created_by_exercises:
                exercises.append(ExerciseSerializer(exercise).data)

            shared_with_exercises = Exercise.objects.filter(
                shared_with=request.user
            )
            for exercise in shared_with_exercises:
                exercises.append(ExerciseSerializer(exercise).data)

        return Response(exercises, status=status.HTTP_200_OK)

    def post(self, request):
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["is_public"] = False
        request.data["created_by"] = request.user.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        if exercise.is_public:
            return Response(
                ExerciseSerializer(exercise).data,
                status=status.HTTP_200_OK,
            )

        if request.user.is_authenticated:
            if (
                exercise.created_by == request.user or
                request.user in exercise.shared_with.all()
            ):
                return Response(
                    ExerciseSerializer(exercise).data,
                    status=status.HTTP_200_OK,
                )

        return Response({'message': 'Exercise is not available'},
                        status=status.HTTP_403_FORBIDDEN)

    def put(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["public"] = False
        request.data["created_by"] = exercise.created_by.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        if (
            request.user.is_authenticated and
            exercise.created_by == request.user
        ):
            serializer = ExerciseSerializer(
                exercise, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': 'You are not authorized to edit this exercise.'},
            status=status.HTTP_403_FORBIDDEN
        )

    def delete(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        if (
            request.user.is_authenticated and
            exercise.created_by == request.user
        ):
            exercise.created_by = None
            exercise.save()
            return Response(
                {
                    'message':
                    'Exercise deleted from ' +
                    'user_created_exercises successfully'
                },
                status=status.HTTP_200_OK
            )
        if (
            request.user.is_authenticated and
            request.user in exercise.shared_with.all()
        ):
            exercise.shared_with.remove(request.user)
            return Response(
                {'message': 'Exercise removed from shared_with successfully'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'message': 'You are not authorized to delete this exercise.'},
            status=status.HTTP_403_FORBIDDEN
        )


class WorkoutExerciseView(APIView):
    http_method_names = ['get', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        return [IsAuthenticated()]

    def get(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        workout_exercises = []

        available_for_workout_exercises = WorkoutExercise.objects.filter(
            available_for=request.user,
            exercise=exercise,
        )
        for workout_exercise in available_for_workout_exercises:
            workout_exercises.append(
                workout_exercise
            )

        response_workout_exercises = []
        new_workout_exercises_data = []

        for workout_exercise in workout_exercises:
            data = [
                    workout_exercise.sets,
                    workout_exercise.reps,
                    workout_exercise.rest_time,
            ]
            if data not in new_workout_exercises_data:
                response_workout_exercises.append(workout_exercise)
                new_workout_exercises_data.append(data)

        response_data = []

        for workout_exercise in response_workout_exercises:
            response_data.append(
                WorkoutExerciseSerializer(workout_exercise).data
            )

        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)

        available_for_workout_exercises = WorkoutExercise.objects.filter(
            available_for=request.user,
            exercise=exercise
        )
        for workout_exercise in available_for_workout_exercises:
            workout_exercise.available_for.remove(request.user)

        return Response(
            {
                'message':
                'WorkoutExercise removed from available_for successfully'
            },
            status=status.HTTP_200_OK
        )


class WorkoutDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)

        if workout.is_public:
            return Response(
                WorkoutSerializer(workout).data,
                status=status.HTTP_200_OK,
            )

        if request.user.is_authenticated:
            if (
                workout.created_by == request.user or
                request.user in workout.shared_with.all()
            ):
                return Response(
                    WorkoutSerializer(workout).data,
                    status=status.HTTP_200_OK,
                )

        return Response({'message': 'Workout is not available'},
                        status=status.HTTP_403_FORBIDDEN)

    def put(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)

        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["public"] = False
        request.data["created_by"] = workout.created_by.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        if (
            request.user.is_authenticated and
            workout.created_by == request.user
        ):
            serializer = WorkoutSerializer(
                workout, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': 'You are not authorized to edit this exercise.'},
            status=status.HTTP_403_FORBIDDEN
        )

    def delete(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)

        if (
            request.user.is_authenticated and
            workout.created_by == request.user
        ):
            if request.data.get('delete_from_all_shared_with', False) == 'true':
                for workout_exercise in workout.workout_exercises.all():
                    workout_exercise.delete()
                workout.delete()
                return Response(
                    {'message': 'Workout deleted successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                workout.created_by = None
                workout.save()
                return Response(
                    {
                        'message':
                        'Workout deleted from ' +
                        'user_created_workouts successfully'
                    },
                    status=status.HTTP_200_OK
                )
        if (
            request.user.is_authenticated and
            request.user in workout.shared_with.all()
        ):
            if request.data.get(
                'delete_all_connected_exercises_and_workout_exercises', False
            ) == 'true':
                for exercise in workout.exercises.all():
                    if request.user in exercise.shared_with.all():
                        exercise.shared_with.remove(request.user)
                    if exercise.created_by == request.user:
                        exercise.created_by = None
                    exercise.save()
                for workout_exercise in workout.workout_exercises.filter(workout=workout):
                    if request.user in workout_exercise.available_for.all():
                        workout_exercise.shared_with.remove(request.user)
            workout.shared_with.remove(request.user)
            return Response(
                {'message': 'Workout removed from shared_with successfully'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'message': 'You are not authorized to delete this exercise.'},
            status=status.HTTP_403_FORBIDDEN
        )


class WorkoutView(APIView):
    http_method_names = ['get', 'post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get(self, request):
        workouts = []

        for workout in Workout.objects.filter(is_public=True):
            workouts.append(WorkoutSerializer(workout).data)

        if request.user.is_authenticated:
            created_by_workouts = Workout.objects.filter(
                created_by=request.user
            )
            for workout in created_by_workouts:
                workouts.append(WorkoutSerializer(workout).data)

            shared_with_workouts = Workout.objects.filter(
                shared_with=request.user
            )
            for workout in shared_with_workouts:
                workouts.append(WorkoutSerializer(workout).data)

        return Response(workouts, status=status.HTTP_200_OK)

    def post(self, request):
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["public"] = False
        request.data["created_by"] = request.user.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        serializer = WorkoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
