import datetime

from django.conf import settings
from django.db import models

# Create your models here.
from api.users.models import User
from main.models import Log


class Event(Log):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_event', null=True)
    date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Event'


class Appointment(Log):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_appointment', null=True)
    events = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_appointment', null=True)
    title = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)
    date = models.DateTimeField(null=True)
    remainder = models.IntegerField(default=5)
    event_id = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'Appointment'

    # def sava(self, *args, **kwargs):
    #     if self.user.access_token:
    #
    #             id = GoogleCalenderManager(self.user.access_token).creat_event(obj)
    #             self.event_id = id
    #         super().save()
    #     except Exception:
    #         raise
    @staticmethod
    def create(validated_data):
        event, is_created = Event.objects.get_or_create(date=validated_data['date'].date(), user_id=validated_data['user_id'])
        validated_data["events_id"] = event.id
        return Appointment.objects.create(**validated_data)

    @staticmethod
    def get_un_sync_appointment(user_id):
        obj = Appointment.objects.filter(event_id__isnull=True, user_id=user_id)
        dic = {}
        for x in obj:
            a = {
                "summary": x.title,
                "description": x.title,
                "start": {
                    "dateTime": x.date.strftime('%Y-%m-%dT%H:%M:%S'),
                    "timeZone": settings.TIME_ZON
                },
                "end": {
                    "dateTime": x.date.strftime('%Y-%m-%dT%H:%M:%S'),
                    "timeZone": settings.TIME_ZON
                },
                "location": x.location,
                'colorId':"7",
                # "attendees": [
                #     {"email": "attendee1@example.com"},
                #     {"email": "attendee2@example.com"}
                # ],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": x.remainder},
                        {"method": "popup", "minutes": x.remainder}
                    ]
                }
            }
            dic[x.id] = a
        return dic
