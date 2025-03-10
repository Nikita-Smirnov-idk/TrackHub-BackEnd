from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.http import QueryDict
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from workout_manager.models import (
    Exercise,
    Workout,
    WorkoutExercise,
    ExerciseCategory,
    GymEquipment,
    WeeklyFitnessPlan,
    WeeklyFitnessPlanWorkout,
)
from workout_manager.serializers import (
    ExerciseSerializer,
    WorkoutSerializer,
    WorkoutExerciseSerializer,
    ExerciseCategorySerializer,
    GymEquipmentSerializer,
    WeeklyFitnessPlanSerializer,
    WeeklyFitnessPlanWorkoutSerializer,
)
from users.models import CustomUser
from rest_framework.parsers import MultiPartParser, FormParser
from workout_manager.Services import originality_service


class ExercisePublishedView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(created_by=request.user, is_published=True)

        serialized_exercises = ExerciseSerializer(exercises, many=True).data

        return Response(serialized_exercises, status=status.HTTP_200_OK)


class ExercisePersonalView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(created_by=request.user, is_archived=False, original=None)

        serialized_exercises = ExerciseSerializer(exercises, many=True).data

        return Response(serialized_exercises, status=status.HTTP_200_OK)


class ExerciseSubcribedView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(created_by=request.user, is_archived=False, original__isnull=False)

        serialized_exercises = ExerciseSerializer(exercises, many=True).data

        return Response(serialized_exercises, status=status.HTTP_200_OK)
    


class ExerciseView(APIView):
    http_method_names = ['get', 'post']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(is_public=True)

        serialized_exercises = ExerciseSerializer(exercises, many=True).data

        return Response(serialized_exercises, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        if exercise.is_public or exercise.created_by == request.user:
            serializer = ExerciseSerializer(exercise)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def put(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        if exercise.created_by == request.user:
            serializer = ExerciseSerializer(exercise, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def delete(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        
        # Check if the exercise is associated with any workouts
        if WorkoutExercise.objects.filter(exercise=exercise).exists():
            return Response(
                {"error": "Данное упражнение используется как минимум в одной тренировке. Измените тренировки и попробуйте ещё раз."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if exercise.is_published:
            if Exercise.objects.filter(original=exercise).exists():
                return Response(
                    {"error": "Данное упражнение опубликовано и имеет подписчиков. Его нельзя удалить."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if exercise.created_by == request.user:
            exercise.delete()
            return Response(
            {"message": "Exercise deleted successfully."},
            status=status.HTTP_200_OK
        )
        
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class ArchivedExerciseView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(created_by=request.user, is_archived=True)

        serialized_exercises = []

        for exercise in exercises:
            serialized_exercises.append(ExerciseSerializer(exercise).data)

        return Response(serialized_exercises, status=status.HTTP_200_OK)

class ArchivedExercisesDetailView(APIView):
    http_method_names = ['patch']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def patch(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        if exercise.created_by == request.user and exercise.original:
            exercise.is_archived = not exercise.is_archived
            exercise.save()

            return Response(
                {"message": "Exercise archived successfully." if exercise.is_archived else "Exercise unarchived successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

class WorkoutPersonalView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        workouts = Workout.objects.filter(created_by=request.user, is_archived=False, original=None)

        serialized_workouts = WorkoutSerializer(workouts, many=True).data

        return Response(serialized_workouts, status=status.HTTP_200_OK)


class WorkoutSubcribedView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        workouts = Workout.objects.filter(created_by=request.user, is_archived=False, original__isnull=False)

        serialized_workouts = WorkoutSerializer(workouts, many=True).data

        return Response(serialized_workouts, status=status.HTTP_200_OK)


class WorkoutView(APIView):
    http_method_names = ['get', 'post']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        workouts = Workout.objects.filter(is_public=True)

        serialized_workouts = WorkoutSerializer(workouts, many=True).data

        return Response(serialized_workouts, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = WorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class WorkoutDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)
        if workout.is_public or workout.created_by == request.user:
            serializer = WorkoutSerializer(workout)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def put(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)
        if workout.created_by == request.user:
            serializer = WorkoutSerializer(workout, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def delete(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)
        
        # Check if the exercise is associated with any workouts
        if WeeklyFitnessPlanWorkout.objects.filter(workout=workout).exists():
            return Response(
                {"error": "Данная тренировка используется как минимум в одном недельном плане. Измените недельные планы и попробуйте ещё раз."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if workout.is_published:
            if Workout.objects.filter(original=workout).exists():
                return Response(
                    {"error": "Данная тренировка опубликована и имеет подписчиков. Ее нельзя удалить."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if workout.created_by == request.user:
            workout.delete()
            return Response(
            {"message": "Workout deleted successfully."},
            status=status.HTTP_200_OK
        )
        
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

class ArchivedWorkoutView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        workouts = Workout.objects.filter(created_by=request.user, is_archived=True)

        serialized_workouts = []

        for workout in workouts:
            serialized_workouts.append(WorkoutSerializer(workout).data)

        return Response(serialized_workouts, status=status.HTTP_200_OK)

class ArchivedWorkoutDetailView(APIView):
    http_method_names = ['patch']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def patch(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)
        if workout.created_by == request.user and workout.original:
            workout.is_archived = not workout.is_archived
            workout.save()

            return Response(
                {"message": "Workout archived successfully." if workout.is_archived else "Workout unarchived successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class WorkoutSubscriptionView(APIView):
    http_method_names = ['post']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def post(self, request, workout_id):
        workout = get_object_or_404(Workout, pk=workout_id)

        if workout.is_published:
            workout.clone_for_user(request.user)

            return Response(
                {"message": "Subscribed on workout successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class WorkoutPublishDetailView(APIView):
    http_method_names = ['post', 'delete']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def post(self, request, workout_id):
        workout = get_object_or_404(Exercise, pk=workout_id)

        count_all, count_not_original = originality_service.get_workout_originality_values(workout.id, request.user.id)

        is_original = originality_service.get_originality(count_all, count_not_original)

        if is_original:
            workout.is_published = True
            workout.save()

            return Response(
                {"message": "Workout published successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Использовано слишком много чужих элементов, низкая оригинальность"}, status=status.HTTP_400_BAD_REQUEST)\
        
    def delete(self, request, workout_id):
        workout = get_object_or_404(Exercise, pk=workout_id)

        if workout.created_by == request.user:
            if Workout.objects.filter(original=workout).exists():
                return Response(
                    {"error": "Данная тренировка опубликована и имеет подписчиков. Ее нельзя удалить из публичных тренировок."},
                    status=status.HTTP_400_BAD_REQUEST
            )

            workout.is_published = False
            workout.save()

            return Response(
                {"message": "Workout unpublished successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

class WorkoutPublishView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        workouts = Workout.objects.filter(is_published=True)

        serialized_plans = []

        for workout in workouts:
            serialized_plans.append(WeeklyFitnessPlanSerializer(workout).data)

        return Response(serialized_plans, status=status.HTTP_200_OK)


class WeeklyFitnessPlanPersonalView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        plans = WeeklyFitnessPlan.objects.filter(created_by=request.user, is_archived=False, original=None)

        serialized_plans = WeeklyFitnessPlanSerializer(plans, many=True).data

        return Response(serialized_plans, status=status.HTTP_200_OK)


class WeeklyFitnessPlanSubcribedView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        plans = Workout.objects.filter(created_by=request.user, is_archived=False, original__isnull=False)

        serialized_plans = WeeklyFitnessPlanSerializer(plans, many=True).data

        return Response(serialized_plans, status=status.HTTP_200_OK)


class WeeklyFitnessPlanView(APIView):
    http_method_names = ['get', 'post']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['POST']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        plans = WeeklyFitnessPlan.objects.filter(is_public=True)

        serialized_plans = WeeklyFitnessPlanSerializer(plans, many=True).data

        return Response(serialized_plans, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = WeeklyFitnessPlanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class WeeklyFitnessPlanDetailView(APIView):
    http_method_names = ['get', 'put', 'delete']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)
        if plan.is_public or plan.created_by == request.user:
            serializer = WeeklyFitnessPlanSerializer(plan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def put(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)
        if plan.created_by == request.user:
            serializer = WeeklyFitnessPlanSerializer(plan, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    def delete(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)
        
        if plan.is_published:
            if WeeklyFitnessPlan.objects.filter(original=plan).exists():
                return Response(
                    {"error": "Данный недельный план опубликован и имеет подписчиков. Его нельзя удалить."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if plan.created_by == request.user:
            plan.delete()
            return Response(
            {"message": "Workout deleted successfully."},
            status=status.HTTP_200_OK
        )
        
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

class ArchivedWeeklyFitnessPlanView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        plans = WeeklyFitnessPlan.objects.filter(created_by=request.user, is_archived=True)

        serialized_plans = []

        for plan in plans:
            serialized_plans.append(WeeklyFitnessPlanSerializer(plan).data)

        return Response(serialized_plans, status=status.HTTP_200_OK)

class ArchivedWeeklyFitnessPlanDetailView(APIView):
    http_method_names = ['patch']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def patch(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)
        if not plan.original:
            return Response({"error": "This plan is original"}, status=status.HTTP_400_BAD_REQUEST)
        if plan.created_by == request.user and plan.original:
            plan.is_archived = not plan.is_archived
            plan.save()

            return Response(
                {"message": "Plan archived successfully." if plan.is_archived else "Plan unarchived successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class WeeklyFitnessPlanSubscriptionView(APIView):
    http_method_names = ['post']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def post(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)

        if plan.is_published:
            plan.clone_for_user(request.user)

            return Response(
                {"message": "Subscribed on plan successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class WeeklyFitnessPlanPublishDetailView(APIView):
    http_method_names = ['get', 'post', 'delete']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def post(self, request, plan_id):
        
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)

        count_all, count_not_original = originality_service.get_plan_originality_values(plan.id, request.user.id)

        is_original = originality_service.get_originality(count_all, count_not_original)

        if is_original:
            plan.is_published = True
            plan.save()

            return Response(
                {"message": "Plan published successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Использовано слишком много чужих элементов, низкая оригинальность"}, status=status.HTTP_400_BAD_REQUEST)\
        
    def delete(self, request, plan_id):
        plan = get_object_or_404(WeeklyFitnessPlan, pk=plan_id)

        if plan.created_by == request.user:
            if WeeklyFitnessPlan.objects.filter(original=plan).exists():
                return Response(
                    {"error": "Данный план опубликован и имеет подписчиков. Его нельзя удалить из публичных планов."},
            )

            plan.is_published = False
            plan.save()

            return Response(
                {"message": "Plan unpublished successfully."},
                status=status.HTTP_200_OK
            )
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)


class WeeklyFitnessPlanPublishView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        plans = WeeklyFitnessPlan.objects.filter(is_published=True)

        serialized_plans = []

        for plan in plans:
            serialized_plans.append(WeeklyFitnessPlanSerializer(plan).data)

        return Response(serialized_plans, status=status.HTTP_200_OK)

class DataForExerciseCreationView(APIView):
    http_method_names = ['get']
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()
    
    def get(self, request):
        gym_equipment = GymEquipment.objects.all()
        exercise_categories = ExerciseCategory.objects.all()

        serialized_gym_equipment = GymEquipmentSerializer(gym_equipment, many=True).data
        serialized_exercise_categories = ExerciseCategorySerializer(exercise_categories, many=True).data
        data = dict()
        data['gym_equipment'] = serialized_gym_equipment
        data['exercise_categories'] = serialized_exercise_categories


        return Response(data, status=status.HTTP_200_OK)