# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import StudentInfo, TelegramClient
from .serializers import StudentInfoSerializer, TelegramClientSerializer


class GetTelegramID(APIView):
    def get(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = StudentInfo.objects.select_related('telegram_client').get(student_id=student_id)
            return Response({'telegram_id': student.telegram_client.telegram_id})
        except StudentInfo.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)


class CreateStudentInfo(APIView):
    def post(self, request):
        serializer = StudentInfoSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({
                'student_id': student.student_id,
                'telegram_id': student.telegram_client.telegram_id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTelegramClient(APIView):
    def post(self, request):
        serializer = TelegramClientSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            return Response({'telegram_id': client.telegram_id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTelegramClient(APIView):
    def get(self, request):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response({'error': 'telegram_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = TelegramClient.objects.get(telegram_id=telegram_id)
            return Response({'telegram_id': client.telegram_id})
        except TelegramClient.DoesNotExist:
            return Response({'error': 'TelegramClient not found'}, status=status.HTTP_404_NOT_FOUND)
