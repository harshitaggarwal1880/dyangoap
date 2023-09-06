import datetime

from django.conf import settings
from django.db import models

# Create your models here.
from api.calendars.models import Event
from api.users.models import User
from main.models import Log


class Symptoms(Log):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_symptoms', db_column='UserId')
    title = models.CharField(max_length=255, null=True)
    description = models.TextField(db_column='Description', null=True)
    severity = models.CharField(max_length=255, db_column='Severity', null=True)
    time = models.TimeField(null=True)
    date = models.DateField(null=True)
    duration = models.TextField(null=True)
    associated_factors = models.TextField(null=True)
    medications_taken = models.TextField(null=True)
    notes = models.TextField(null=True)
    triggers = models.TextField(null=True)
    body_part = models.CharField(max_length=255, null=True)
    factor_other = models.CharField(max_length=255, null=True)
    triger_other = models.CharField(max_length=255, null=True)
    event_id = models.TextField(max_length=255, null=True)
    events = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_symptoms', null=True)

    class Meta:
        db_table = 'Symptoms'

    @staticmethod
    def create(validated_data):
        event, is_created = Event.objects.get_or_create(date=validated_data['date'], user_id=validated_data['user_id'])
        validated_data["events_id"] = event.id
        return Symptoms.objects.create(**validated_data)

    @staticmethod
    def get_un_sync_appointment(user_id):
        obj = Symptoms.objects.filter(event_id__isnull=True, user_id=user_id)
        dic = {}
        for x in obj:
            a = {
                "summary": x.title,
                "description": x.title,
                "start": {
                    "dateTime": datetime.datetime.combine(x.date, x.time).strftime('%Y-%m-%dT%H:%M:%S'),
                    "timeZone": settings.TIME_ZON
                },
                "end": {
                    "dateTime": datetime.datetime.combine(x.date, x.time).strftime('%Y-%m-%dT%H:%M:%S'),
                    "timeZone": settings.TIME_ZON
                },
                "location": "",
                "colorId":"11",
                # "attendees": [
                #     {"email": "attendee1@example.com"},
                #     {"email": "attendee2@example.com"}
                # ],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 10},
                        {"method": "popup", "minutes": 10}
                    ]
                }
            }
            dic[x.id] = a
        return dic
