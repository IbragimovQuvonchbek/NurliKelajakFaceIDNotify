# urls.py
from django.urls import path
from .views import GetTelegramID, CreateStudentInfo, CreateTelegramClient, GetTelegramClient

urlpatterns = [
    path('get-telegram-id/', GetTelegramID.as_view(), name='get-telegram-id'),
    path('student-create/', CreateStudentInfo.as_view(), name='student-create'),
    path('telegram-create/', CreateTelegramClient.as_view(), name='telegram-create'),
    path('telegram-get/', GetTelegramClient.as_view(), name='telegram-get'),
]
