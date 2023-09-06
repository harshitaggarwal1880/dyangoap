import os
import threading
from datetime import date, datetime, timedelta
import datetime as c
import django

from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import render

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medication.settings.base")
django.setup()
from medication.utils import send_email
from django.conf import settings
from django.db import models
from django.db.models import Q, Case, When, Value, F
from django.db.models.functions import ExtractDay
from django.utils.text import slugify

from api.calendars.models import Appointment
from api.calendars.serializer import AppointmentSerializer
from api.medicine.models import Medicine
from api.medicine.serializer import MedicineSerializer, MedicineRemainderSerializer


def send_email_thread():
    t1 = threading.Thread(target=send_remainder())
    t1.start()


def send_remainder():
    try:
        s = date.today()
        query = Q(start_from__lte=date.today()) & Q(end_to__gte=s) & Q(is_active=True, )
        medi_query_set = Medicine \
            .objects \
            .filter(query) \
            .annotate(
            divisor=Case(
                When(frequency='daily', then=Value(1)),
                When(frequency='weekly', then=Value(7)),
                default=Value(30),
                output_field=models.IntegerField()
            )
        ).annotate(days=(ExtractDay(s - (F('start_from')))), )
        arr = []
        for x in medi_query_set:
            if x.days % x.divisor == 0:
                arr.append(x)

        serializer1 = MedicineRemainderSerializer(arr, many=True)
        appointment_query_set = Appointment.objects.filter(date__date=date.today())
        # serializer2 = AppointmentSerializer(appointment_query_set, many=True)

        for x in appointment_query_set:
            curr = datetime.now() + timedelta(minutes=x.remainder)
            time = curr.strftime("%H%M")
            # a = date_time_obj = c.datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S')
            a = x.date.strftime("%H%M")
            if a == time:
                context = {
                    'recipient_name': x.user.first_name,
                    'appointment_date': str(x.date),
                    'appointment_location': x.location
                }


                send_email(
                    from_=settings.EMAIL_HOST_USER,
                    send_to=x.user.email,
                    html_template='appointment.html',
                    context=context,
                    subject='Medication Dosage Reminder'

                )

            # if datetime.now().date() ==
        for x in serializer1.data:
            curr = datetime.now() + timedelta(minutes=x['remainder_time'])
            time = curr.strftime("%H%M")
            for y in x['medicine_dosage']:
                a, b, _ = y['time'].split(':')
                a = str(a) + str(b)
                if a == time:
                    context = {
                        'recipient_name': x['user_name'],
                        'medication_name': x['name'],
                        # 'dosage_details': dosage_details,
                        # 'dosage_frequency': dosage_frequency,
                        # 'your_name': your_name,
                        # 'your_contact_information': your_contact_information,
                    }

                    email_subject = 'Medication Dosage Reminder'
                    send_email(
                        from_=settings.EMAIL_HOST_USER,
                        send_to=x['email'],
                        html_template='dosage_remainder.html',
                        context=context,
                        subject='Medication Dosage Reminder'

                    )
                    # email_body = render(request, 'medication_reminder_email.html', context)


    except Exception as e:
        print(e)


if __name__ == '__main__':
    send_email_thread()
