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


class ExerciseView(APIView):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get(self, request):
        exercises = Exercise.objects.filter(is_public=True)
        exercises += Exercise.objects.filter(created_by=request.user)

        serialized_exercises = []

        for exercise in exercises:
            serialized_exercises.append(ExerciseSerializer(exercise).data)

        return Response(serialized_exercises, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, exercise_id):




# class ExerciseView(APIView):
#     http_method_names = ['get', 'post']
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]

#     def get_permissions(self):
#         if self.request.method == 'GET':
#             # Allow any user to access GET requests
#             return [AllowAny()]
#         # Require authentication for other methods
#         return [IsAuthenticated()]

#     def get(self, request):
#         exercises = []

#         for exercise in Exercise.objects.filter(is_public=True):
#             exercises.append(ExerciseSerializer(exercise).data)

#         if request.user.is_authenticated:
#             same_email_users = CustomUser.objects.filter(
#                 email=request.user.email
#             )
#             # ------ changed part for same email users ------
#             for user in same_email_users:
#                 created_by_exercises = Exercise.objects.filter(
#                     created_by=user
#                 )
#                 for exercise in created_by_exercises:
#                     exercises.append(ExerciseSerializer(exercise).data)

#                 shared_with_exercises = Exercise.objects.filter(
#                     shared_with=user
#                 )
#                 for exercise in shared_with_exercises:
#                     exercises.append(ExerciseSerializer(exercise).data)
#             # ------ end of part for same email users ------

#         return Response(exercises, status=status.HTTP_200_OK)

#     def post(self, request):
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = True
#         request.data["is_public"] = False
#         request.data["created_by"] = request.user.id
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = False

#         serializer = ExerciseSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(
#                 serializer.data, status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ExerciseDetailView(APIView):
#     http_method_names = ['get', 'put', 'delete']
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]

#     def get_permissions(self):
#         if self.request.method == 'GET':
#             # Allow any user to access GET requests
#             return [AllowAny()]
#         # Require authentication for other methods
#         return [IsAuthenticated()]

#     def get(self, request, exercise_id):
#         exercise = get_object_or_404(Exercise, pk=exercise_id)

#         if exercise.is_public:
#             return Response(
#                 ExerciseSerializer(exercise).data,
#                 status=status.HTTP_200_OK,
#             )

#         if request.user.is_authenticated:
#             if (
#                 # ------ changed part for same email users ------
#                 check_user_in_created_or_shared(
#                     user=request.user,
#                     created_by=exercise.created_by,
#                     shared_with=exercise.shared_with.all()
#                 )
#                 # ------ end of part for same email users ------
#             ):
#                 return Response(
#                     ExerciseSerializer(exercise).data,
#                     status=status.HTTP_200_OK,
#                 )

#         return Response({'message': 'Exercise is not available'},
#                         status=status.HTTP_403_FORBIDDEN)

#     def put(self, request, exercise_id):
#         exercise = get_object_or_404(Exercise, pk=exercise_id)

#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = True
#         request.data["public"] = False
#         request.data["created_by"] = exercise.created_by.id
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = False

#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                 user=request.user,
#                 created_by=exercise.created_by,
#             )
#             # ------ end of part for same email users ------
#         ):
#             serializer = ExerciseSerializer(
#                 exercise, data=request.data, partial=True
#             )
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data,
#                                 status=status.HTTP_200_OK)
#             return Response(
#                 serializer.errors, status=status.HTTP_400_BAD_REQUEST
#             )

#         return Response(
#             {'message': 'You are not authorized to edit this exercise.'},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     def delete(self, request, exercise_id):
#         exercise = get_object_or_404(Exercise, pk=exercise_id)

#         # ------ changed part for same email users ------
#         same_email_users = CustomUser.objects.filter(
#             email=request.user.email
#         )
#         # ------ end of part for same email users ------

#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                     user=request.user,
#                     created_by=exercise.created_by,
#                     same_email_users=same_email_users,
#             )
#             # ------ end of part for same email users ------
#         ):
#             exercise.created_by = None
#             exercise.save()
#             return Response(
#                 {
#                     'message':
#                     'Exercise deleted from ' +
#                     'user_created_exercises successfully'
#                 },
#                 status=status.HTTP_200_OK
#             )
#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                     user=request.user,
#                     shared_with=exercise.shared_with.all(),
#             )
#             # ------ end of part for same email users ------
#         ):
#             # ------ changed part for same email users ------
#             for user in same_email_users:
#                 exercise.shared_with.remove(user)
#             # ------ end of part for same email users ------
#             return Response(
#                 {'message': 'Exercise removed from shared_with successfully'},
#                 status=status.HTTP_200_OK
#             )

#         return Response(
#             {'message': 'You are not authorized to delete this exercise.'},
#             status=status.HTTP_403_FORBIDDEN
#         )


# class WorkoutExerciseView(APIView):
#     http_method_names = ['get', 'delete']
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]

#     def get_permissions(self):
#         return [IsAuthenticated()]

#     def get(self, request, exercise_id):
#         exercise = get_object_or_404(Exercise, pk=exercise_id)

#         workout_exercises = []

#         # ------ changed part for same email users ------
#         same_email_users = CustomUser.objects.filter(
#             email=request.user.email
#         )

#         for user in same_email_users:
#             available_for_workout_exercises = WorkoutExercise.objects.filter(
#                 available_for=user,
#                 exercise=exercise,
#             )
#             for workout_exercise in available_for_workout_exercises:
#                 workout_exercises.append(
#                     workout_exercise
#                 )
#         # ------ end of part for same email users ------

#         response_workout_exercises = []
#         new_workout_exercises_data = []

#         for workout_exercise in workout_exercises:
#             data = [
#                     workout_exercise.sets,
#                     workout_exercise.reps,
#                     workout_exercise.rest_time,
#             ]
#             if data not in new_workout_exercises_data:
#                 response_workout_exercises.append(workout_exercise)
#                 new_workout_exercises_data.append(data)

#         response_data = []

#         for workout_exercise in response_workout_exercises:
#             response_data.append(
#                 WorkoutExerciseSerializer(workout_exercise).data
#             )

#         return Response(response_data, status=status.HTTP_200_OK)

#     def delete(self, request, exercise_id):
#         exercise = get_object_or_404(Exercise, pk=exercise_id)

#         # ------ part for same email users ------
#         same_email_users = CustomUser.objects.filter(
#             email=request.user.email
#         )
#         for user in same_email_users:
#             available_for_workout_exercises = WorkoutExercise.objects.filter(
#                 available_for=user,
#                 exercise=exercise
#             )
#             for workout_exercise in available_for_workout_exercises:
#                 workout_exercise.available_for.remove(user)
#         # ------ end of part for same email users ------

#         return Response(
#             {
#                 'message':
#                 'WorkoutExercise removed from available_for successfully'
#             },
#             status=status.HTTP_200_OK
#         )


# class WorkoutDetailView(APIView):
#     http_method_names = ['get', 'put', 'delete']
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]

#     def get_permissions(self):
#         if self.request.method == 'GET':
#             # Allow any user to access GET requests
#             return [AllowAny()]
#         # Require authentication for other methods
#         return [IsAuthenticated()]

#     def get(self, request, workout_id):
#         workout = get_object_or_404(Workout, pk=workout_id)

#         if workout.is_public:
#             return Response(
#                 WorkoutSerializer(workout).data,
#                 status=status.HTTP_200_OK,
#             )

#         if request.user.is_authenticated:
#             if (
#                 # ------ changed part for same email users ------
#                 check_user_in_created_or_shared(
#                     created_by=workout.created_by,
#                     shared_with=workout.shared_with.all(),
#                     user=request.user,
#                 )
#                 # ------ end of part for same email users ------
#             ):
#                 return Response(
#                     WorkoutSerializer(workout).data,
#                     status=status.HTTP_200_OK,
#                 )

#         return Response({'message': 'Workout is not available'},
#                         status=status.HTTP_403_FORBIDDEN)

#     def put(self, request, workout_id):
#         workout = get_object_or_404(Workout, pk=workout_id)

#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = True
#         request.data["public"] = False
#         request.data["created_by"] = workout.created_by.id
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = False

#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                 user=request.user,
#                 created_by=workout.created_by,
#             )
#             # ------ end of part for same email users ------
#         ):
#             serializer = WorkoutSerializer(
#                 workout, data=request.data, partial=True
#             )
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data,
#                                 status=status.HTTP_200_OK)
#             return Response(
#                 serializer.errors, status=status.HTTP_400_BAD_REQUEST
#             )

#         return Response(
#             {'message': 'You are not authorized to edit this exercise.'},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     def delete(self, request, workout_id):
#         workout = get_object_or_404(Workout, pk=workout_id)

#         # ------ changed part for same email users ------
#         same_email_users = CustomUser.objects.filter(
#             email=request.user.email
#         )
#         # ------ end of part for same email users ------

#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                 user=request.user,
#                 created_by=workout.created_by,
#                 same_email_users=same_email_users,
#             )
#             # ------ end of part for same email users ------
#         ):
#             if request.data.get(
#                 'delete_from_all_shared_with', False
#             ) == 'true':
#                 for workout_exercise in workout.workout_exercises.all():
#                     workout_exercise.delete()
#                 workout.delete()
#                 return Response(
#                     {'message': 'Workout deleted successfully'},
#                     status=status.HTTP_200_OK
#                 )
#             else:
#                 workout.created_by = None
#                 workout.save()
#                 return Response(
#                     {
#                         'message':
#                         'Workout deleted from ' +
#                         'user_created_workouts successfully'
#                     },
#                     status=status.HTTP_200_OK
#                 )
#         if (
#             request.user.is_authenticated and
#             # ------ changed part for same email users ------
#             check_user_in_created_or_shared(
#                 user=request.user,
#                 shared_with=workout.shared_with.all(),
#             )
#             # ------ end of part for same email users ------
#         ):
#             if request.data.get(
#                 'delete_all_connected_exercises_and_workout_exercises', False
#             ) == 'true':
#                 # ------ changed part for same email users ------
#                 for user in same_email_users:
#                     for exercise in workout.exercises.all():
#                         if user in exercise.shared_with.all():
#                             exercise.shared_with.remove(user)
#                         if exercise.created_by == user:
#                             exercise.created_by = None
#                         exercise.save()
#                     for workout_exercise in workout.workout_exercises.filter(
#                         workout=workout
#                     ):
#                         if user in workout_exercise.available_for.all():
#                             workout_exercise.shared_with.remove(user)
#             for user in same_email_users:
#                 if user in workout.shared_with.all():
#                     workout.shared_with.remove(request.user)
#             # ------ end of part for same email users ------
#             return Response(
#                 {'message': 'Workout removed from shared_with successfully'},
#                 status=status.HTTP_200_OK
#             )

#         return Response(
#             {'message': 'You are not authorized to delete this exercise.'},
#             status=status.HTTP_403_FORBIDDEN
#         )


# class WorkoutView(APIView):
#     http_method_names = ['get', 'post']
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [JWTAuthentication]

#     def get_permissions(self):
#         if self.request.method == 'GET':
#             # Allow any user to access GET requests
#             return [AllowAny()]
#         # Require authentication for other methods
#         return [IsAuthenticated()]

#     def get(self, request):
#         workouts = []

#         # ------ changed part for same email users ------
#         same_email_users = CustomUser.objects.filter(
#             email=request.user.email
#         )
#         # ------ end of part for same email users ------

#         for workout in Workout.objects.filter(is_public=True):
#             workouts.append(WorkoutSerializer(workout).data)

#         if request.user.is_authenticated:
#             # ------ changed part for same email users ------
#             for user in same_email_users:
#                 created_by_workouts = Workout.objects.filter(
#                     created_by=user
#                 )
#                 for workout in created_by_workouts:
#                     workouts.append(WorkoutSerializer(workout).data)

#                 shared_with_workouts = Workout.objects.filter(
#                     shared_with=user
#                 )
#                 for workout in shared_with_workouts:
#                     workouts.append(WorkoutSerializer(workout).data)
#             # ------ end of part for same email users ------

#         return Response(workouts, status=status.HTTP_200_OK)

#     def post(self, request):
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = True
#         request.data["public"] = False
#         request.data["created_by"] = request.user.id
#         if isinstance(request.data, QueryDict):  # optional
#             request.data._mutable = False

#         serializer = WorkoutSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
