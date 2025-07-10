from django.db import models
from datetime import datetime


class TelegramClient(models.Model):
    telegram_id = models.CharField(max_length=255, null=False, blank=False, unique=True)
    created_at = models.DateField(default=datetime.now)

    def __str__(self):
        return self.telegram_id


class StudentInfo(models.Model):
    student_id = models.CharField(max_length=255, null=False, blank=False, unique=True)
    created_at = models.DateField(default=datetime.now)
    telegram_client = models.ForeignKey(TelegramClient, on_delete=models.CASCADE)

    def __str__(self):
        return self.student_id
