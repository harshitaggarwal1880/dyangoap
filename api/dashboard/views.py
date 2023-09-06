import datetime
from datetime import date
import calendar

from django.db import models
from django.db.models import Q, F, Case, When, Value, Sum, Count, Prefetch
from django.db.models.functions import ExtractDay, TruncMonth, TruncWeek
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from django.db.models.functions import ExtractWeekDay
from api.calendars.models import Appointment
from api.calendars.serializer import AppointmentSerializer
from api.medicine.models import Medicine, DosageTime, DosageHistory
from api.medicine.serializer import MedicineSerializer
from api.permissions import IsOauthAuthenticatedCustomer
from api.views import BaseAPIView
from medication.utils import search_array_of_dict


class DashboardView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsOauthAuthenticatedCustomer, ]

    def get(self, request):
        try:
            s = date.today()
            query = Q(user_id=request.user.id, ) & Q(is_active=True, )
            medi_query_set = Medicine \
                .objects .prefetch_related(
                    Prefetch(
                        "medicine_dosage",
                        queryset=DosageTime.objects.filter(is_active=True)
                    ))\
                .filter(query, medicine_event__event__date=s).distinct() \
            #     .annotate(
            #     divisor=Case(
            #         When(frequency='daily', then=Value(1)),
            #         When(frequency='weekly', then=Value(7)),
            #         default=Value(30),
            #         output_field=models.IntegerField()
            #     )
            # ).annotate(day=(ExtractDay(s - (F('start_from')))), )
            # arr = []
            # for x in medi_query_set:
            #     if x.day % x.divisor == 0:
            #         arr.append(x)

            serializer1 = MedicineSerializer(medi_query_set, many=True)
            appointment_query_set = Appointment.objects.filter(date__date=date.today(), user_id=request.user.id)
            serializer2 = AppointmentSerializer(appointment_query_set, many=True)
            # total = Medicine.objects.filter(is_active=True, user_id=request.user.id).aggregate(medi=Sum('quantity'))[
            #     'medi']
            # total = total if total else 0
            # taken = DosageTime.objects.filter(is_active=True, medicine__is_active=True,
            #                                   medicine__user_id=request.user.id).count()

            taken, pending = 0, 0
            for x in serializer1.data:
                for y in x['medicine_dosage']:
                    if y['taken']:
                        taken += 1
                    else:
                        pending += 1
            # Monthly
            taken_monthly = DosageHistory. \
                objects.filter(dosage__medicine__is_active=True, dosage__medicine__user_id=request.user.id). \
                annotate(month=TruncMonth('date')) \
                .values('month') \
                .annotate(c=Count('id')) \
                .values('month', 'c')
            taken_weekly = DosageHistory \
                .objects \
                .filter(
                dosage__medicine__is_active=True,
                dosage__medicine__user_id=request.user.id,
                date__range=[date.today() - datetime.timedelta(days=7), date.today()]
            ) \
                .annotate(week=F('date')) \
                .values('week') \
                .annotate(c=Count('id')) \
                .values('week', 'c')

            total_by_month = DosageTime.get_total_dose_by_month(request.user.id)
            total_by_week = DosageTime.get_total_dose_by_week(request.user.id)
            monthly = []
            weekly = []
            for x in total_by_month:
                s = search_array_of_dict(taken_monthly, 'month', x['month'], is_month=True)
                t = 0
                if s:
                    t = s['c']
                monthly.append(
                    {
                        "month": x['month'],
                        "taken": t,
                        "missed": 0 if x["c"] - t < 0 else x["c"] - t
                    }
                )
            for x in total_by_week:
                s = search_array_of_dict(taken_weekly, 'week', x['week'], is_month=False)
                t = 0
                if s:
                    t = s['c']
                weekly.append(
                    {
                        "week": x['week'],
                        "taken": t,
                        "missed": 0 if x["c"] - t < 0 else x["c"] - t
                    }
                )
            # for x, y in zip(total_by_week, taken_weekly):
            #     monthly.append(
            #         {
            #             "week": y['weekday'],
            #             "taken": y['c'],
            #             "missed": x["c"] - y['c']
            #         }
            #     )
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                payload={
                    "appointment": serializer2.data,
                    "medicine": serializer1.data,
                    "taken": taken,
                    "pending": pending,
                    "monthly": monthly,
                    "weekly": weekly
                }
            )

        except Exception as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                description=str(e)
            )
