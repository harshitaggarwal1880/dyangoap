import datetime
from datetime import date

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from dateutil.relativedelta import relativedelta
# Create your models here.
from api.calendars.models import Event
from api.users.models import User
from main.models import Log

import calendar

week = {
    "monday": 1,
    "tuesday": 2,
    'wednesday': 3,
    'thursday': 4,
    'friday': 5,
    'saturday': 6,
    'sunday': 7
}


class MedicineFrequency:
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    OTHERS = 'others'


class Remainder:
    EMAIL = 'email'
    POPUP = 'popup'


class Medicine(Log):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_medicine')
    name = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=255, null=True)
    dosage_amount = models.IntegerField(null=True)
    unit = models.CharField(max_length=255, null=True)
    frequency = models.CharField(max_length=255, null=True)

    end_to = models.DateField(null=True)
    meal = models.CharField(max_length=255, null=True)
    instructions = models.TextField(null=True)
    reminders = models.CharField(max_length=255, null=True)
    image = models.ImageField(null=True)
    additional_notes = models.TextField(null=True)
    start_from = models.DateField(null=True)

    remainder_time = models.IntegerField(default=5)
    forgot_remainder = models.IntegerField(default=5)

    quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    medication_type_other = models.TextField(null=True)
    custom_frequency = models.TextField(null=True)
    days = ArrayField(base_field=models.CharField(max_length=20, null=True), size=7, null=True)

    class Meta:
        db_table = 'Medicine'

    def get_quantity(self):
        return self.quantity - DosageHistory.objects.filter(dosage__medicine_id=self.id).count()

    @staticmethod
    def creat_events(medicine):

        if medicine.frequency == MedicineFrequency.OTHERS:

            for x in medicine.days:
                a = week[x] - medicine.start_from.isoweekday()
                if a < 0:
                    a = (a + 7) % 8
                else:
                    a = abs(a)
                start = medicine.start_from + datetime.timedelta(days=a)
                days = (medicine.end_to - start).days
                while days >= 0:
                    obj, _ = Event.objects.get_or_create(date=start, user_id=medicine.user.id)
                    EventMedication.objects.get_or_create(event_id=obj.id, medicine_id=medicine.id)
                    start = start + datetime.timedelta(days=7)
                    days -= 7

        else:
            if medicine.end_to:
                days = (medicine.end_to - medicine.start_from).days

            else:
                days = medicine.quantity

            # if medicine.frequency == MedicineFrequency:
            #     a = medicine.start_from.isoweekday()-
            daye_time = medicine.start_from
            while days >= 0:
                event, is_created = Event.objects.get_or_create(user_id=medicine.user.id, date=daye_time)
                EventMedication.objects.create(event_id=event.id, medicine_id=medicine.id)
                if medicine.frequency == MedicineFrequency.DAILY:
                    days -= 1
                    daye_time = daye_time + datetime.timedelta(days=1)

                elif medicine.frequency == MedicineFrequency.WEEKLY:
                    daye_time = daye_time + datetime.timedelta(days=7)
                    days -= 7
                elif medicine.frequency == MedicineFrequency.MONTHLY:
                    daye_time = daye_time + datetime.timedelta(days=30)
                    days -= 30

            # elif medicine.frequency==MedicineFrequency.OTHERS:

    #
    # def is_enable(self):
    #     return True if self.medicine_dosage.first().is_enable() else False


class DosageTime(Log):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, related_name='medicine_dosage')
    time = models.TimeField(null=True)
    is_active = models.BooleanField(default=True, null=True)
    day = models.CharField(max_length=255, null=True)
    event_id = models.TextField(null=True)

    class Meta:
        db_table = 'DosageTime'

    def is_taken(self):
        data = datetime.date.today()
        routine = self.medicine.frequency
        if routine == MedicineFrequency.DAILY:
            return True if self.dosage_history.filter(date=data).exists() else False
        if routine == MedicineFrequency.OTHERS:
            event = EventMedication.objects.filter(medicine_id=self.medicine.id, event__date=date.today())
            return True if event.exists() and self.dosage_history.filter(date=data).exists() else False
        else:
            event = EventMedication.objects.filter(medicine_id=self.medicine.id, event__date=date.today())
            return True if event.exists() and self.dosage_history.filter(date=data).exists() else False
            # days = 7 if self.medicine.frequency == MedicineFrequency.WEEKLY else 30
            # last_dosage = self.dosage_history.last()
            # if last_dosage:
            #     return False if last_dosage.date + datetime.timedelta(days=days) == data else True
            # else:
            #     return False if self.medicine.start_from == data else True

    @staticmethod
    def get_un_sync_dosage(user_id):
        dic = {}
        obj = DosageTime \
            .objects \
            .filter(
            event_id__isnull=True,
            is_active=True,
            medicine__is_active=True,
            medicine__user_id=user_id
        )
        for x in obj:
            if x.medicine.frequency == MedicineFrequency.OTHERS:
                arr = []
                for y in x.medicine.days:
                    a = week[y] - x.medicine.start_from.isoweekday()
                    if a < 0:
                        a = (a + 7) % 8
                    else:
                        a = abs(a)
                    start = x.medicine.start_from + datetime.timedelta(days=a)
                    days = (x.medicine.end_to - start).days
                    while days >= 0:
                        a = {
                            "summary": x.medicine.name,
                            "description": x.medicine.name,
                            "start": {
                                "dateTime": datetime.datetime.combine(start, x.time).strftime('%Y-%m-%dT%H:%M:%S'),
                                "timeZone": settings.TIME_ZON
                            },
                            "end": {
                                "dateTime": datetime.datetime.combine(start, x.time).strftime('%Y-%m-%dT%H:%M:%S'),
                                "timeZone": settings.TIME_ZON
                            },
                            "location": "Event Location",
                            "colorId": 5,
                            # "attendees": [
                            #     {"email": "attendee1@example.com"},
                            #     {"email": "attendee2@example.com"}
                            # ],
                            "reminders": {
                                "useDefault": False,
                                "overrides": [
                                    {"method": "email", "minutes": x.medicine.remainder_time},
                                    {"method": "popup", "minutes": x.medicine.remainder_time}
                                ]
                            }
                        }

                        start = start + datetime.timedelta(days=7)
                        days -= 7
                        arr.append(a)

                dic[x.id] = arr
            else:
                arr = []
                if x.medicine.end_to:
                    days = (x.medicine.end_to - x.medicine.start_from).days
                else:
                    days = x.medicine.quantity

                daye_time = datetime.datetime.combine(x.medicine.start_from, x.time)
                while days >= 0:

                    a = {
                        "summary": x.medicine.name,
                        "description": x.medicine.name,
                        "start": {
                            "dateTime": daye_time.strftime('%Y-%m-%dT%H:%M:%S'),
                            "timeZone": settings.TIME_ZON
                        },
                        "end": {
                            "dateTime": daye_time.strftime('%Y-%m-%dT%H:%M:%S'),
                            "timeZone": settings.TIME_ZON
                        },
                        "location": "Event Location",
                        "colorId": 5,
                        # "attendees": [
                        #     {"email": "attendee1@example.com"},
                        #     {"email": "attendee2@example.com"}
                        # ],
                        "reminders": {
                            "useDefault": False,
                            "overrides": [
                                {"method": "email", "minutes": x.medicine.remainder_time},
                                {"method": "popup", "minutes": x.medicine.remainder_time}
                            ]
                        }
                    }
                    arr.append(a)
                    if x.medicine.frequency == MedicineFrequency.DAILY:
                        days -= 1
                        daye_time = daye_time + datetime.timedelta(days=1)

                    if x.medicine.frequency == MedicineFrequency.WEEKLY:
                        daye_time = daye_time + datetime.timedelta(days=7)
                        days -= 7
                    if x.medicine.frequency == MedicineFrequency.MONTHLY:
                        daye_time = daye_time + datetime.timedelta(days=30)
                        days -= 30
                dic[x.id] = arr

        return dic

    @staticmethod
    def get_total_dose_by_month(user_id):
        try:
            month = []
            data = []
            start = EventMedication.objects.filter(is_active=True, medicine__user_id=user_id,
                                                   medicine__is_active=True).order_by(
                "event__date").first().event.date
            # start = Medicine.objects.filter(is_active=True, user_id=user_id).order_by("start_from").first().start_from
            end = date.today()
            month.append(start)
            while start.month < end.month:
                start += relativedelta(months=1)
                month.append(start)
            for x in month:
                count = 0
                for y in EventMedication \
                        .objects.filter(is_active=True, medicine__user_id=user_id, event__date__month=x.month,
                                        medicine__is_active=True).exclude(event__date=date.today()):
                    days = 1
                    count += y.medicine.medicine_dosage.filter(is_active=True).count() * days

                # if x + datetime.timedelta(days=30) <= y.end_to:
                #     days = 30
                # else:
                #     days = (date.today() - y.start_from).days
                # # days =1 if days==0 else days
                # if y.frequency == MedicineFrequency.MONTHLY:
                #     days = 1
                # if y.frequency == MedicineFrequency.WEEKLY:
                #     days = days / 7
                data.append({
                    "month": x,
                    "c": count
                })
            return data




        except:
            return []

    @staticmethod
    def get_total_dose_by_week(user_id):
        try:
            month = []
            data = []
            week = 1
            start = date.today() - datetime.timedelta(days=7)
            end = date.today()
            month.append(start)
            # start += datetime.timedelta(days=7)
            while start < end:
                start += datetime.timedelta(days=1)
                if start > end:
                    start = end
                month.append(start)
            for x in month:
                count = 0
                for y in EventMedication.objects.filter(
                        is_active=True, medicine__user_id=user_id,
                        event__date=x
                ):
                    days = 1
                    # if x + datetime.timedelta(days=7) <= y.end_to:
                    #     days = 7
                    # else:
                    #     days = (date.today() - y.start_from).days
                    #     # days = 1 if days == 0 else days
                    # if y.frequency == MedicineFrequency.MONTHLY:
                    #     days = 0
                    # if y.frequency == MedicineFrequency.WEEKLY:
                    #     days = 1
                    count += y.medicine.medicine_dosage.filter(is_active=True).count() * days
                data.append({
                    "week": x,
                    "c": count
                })
                week += 1
            return data




        except:
            return []


class DosageHistory(Log):
    dosage = models.ForeignKey(DosageTime, on_delete=models.CASCADE, null=True, related_name='dosage_history')
    date = models.DateField(null=True)


class Images(models.Model):
    image = models.FileField(db_column="File", default=None, null=True)

    class Meta:
        db_table = 'Wiztap_Images'


class EventMedication(Log):
    medicine = models.ForeignKey(Medicine, related_name='medicine_event', on_delete=models.CASCADE, null=True)
    event = models.ForeignKey(Event, related_name='event_medicine', on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "EventMedication"
