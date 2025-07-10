# serializers.py
from rest_framework import serializers
from .models import StudentInfo, TelegramClient


class StudentTelegramSerializer(serializers.ModelSerializer):
    telegram_id = serializers.CharField(source='telegram_client.telegram_id')

    class Meta:
        model = StudentInfo
        fields = ['student_id', 'telegram_id']


class TelegramClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramClient
        fields = ['telegram_id']


class StudentInfoSerializer(serializers.ModelSerializer):
    telegram_id = serializers.CharField(write_only=True)

    class Meta:
        model = StudentInfo
        fields = ['student_id', 'telegram_id']

    def create(self, validated_data):
        telegram_id = validated_data.pop('telegram_id')
        telegram_client, _ = TelegramClient.objects.get_or_create(telegram_id=telegram_id)
        return StudentInfo.objects.create(telegram_client=telegram_client, **validated_data)


