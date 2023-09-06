from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from api.calendars.models import Appointment, Event
from api.calendars.serializer import AppointmentSerializer, EventSerializer
from api.medicine.models import DosageTime, Medicine, EventMedication
from api.permissions import IsOauthAuthenticatedCustomer
from api.symptoms.models import Symptoms
from api.users.models import User
from api.views import BaseAPIView
from medication.utils import GoogleCalenderManager


class AppointmentView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # category_id = request.query_params.get('category-id', None)
            # search = request.query_params.get('search', None)
            # publish = request.query_params.get('publish', None)
            # out_stock = request.query_params.get('out-of-stock', None)
            # low_thresh = request.query_params.get('low-thresh', None)
            # is_active = request.query_params.get('is-active', None)
            #  drop-dow params shows only parent products
            # listing = request.query_params.get('drop-down', None)

            query_set = Q(user_id=request.user.id)

            if pk:
                query_set &= Q(id=pk)
                query = Appointment.objects.get(query_set)
                serializer = AppointmentSerializer(query)
                count = 1
            else:
                query = Appointment.objects.filter(query_set).order_by('-id')

                serializer = AppointmentSerializer(
                    query[offset:limit + offset],
                    many=True,

                )
                count = query.count()
            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                payload=serializer.data,
                count=count
            )
        except Appointment.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description='Appointment Does`t Exist'
            )
        except FieldError as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=f'422',
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=e
            )

    def post(self, request):
        try:
            with transaction.atomic():
                serializer = AppointmentSerializer(data=request.data)
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    validated_data["user_id"] = request.user.id
                    serializer.save(**validated_data)
                    return self.send_response(
                        success=True,
                        code=f'201',
                        status_code=status.HTTP_201_CREATED,
                        description='Appointment Added Successfully',

                    )
                else:
                    return self.send_response(
                        success=False,
                        code=f'422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        description=serializer.errors
                    )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )

        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                if "StockKeepingUnit" in e.args[0]:
                    message = "Syptom exists in the system"
                else:
                    message = "Product with this name or slug already exists in the system."
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=message
                )

            return self.send_response(
                code=f'500',
                description=str(e)
            )

    # def put(self, request, pk=None):
    #     try:
    #         serializer = SymptomsSerializer(
    #             instance=Symptoms.objects.get(id=pk),
    #             data=request.data,
    #             partial=True
    #         )
    #         if serializer.is_valid():
    #             serializer.save()
    #             return self.send_response(
    #                 success=True,
    #                 code=f'201',
    #                 status_code=status.HTTP_201_CREATED,
    #                 description='Symptom Updated Successfully',
    #
    #             )
    #         else:
    #             return self.send_response(
    #                 success=False,
    #                 code=f'422',
    #                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #                 description=serializer.errors
    #             )
    #     except Symptoms.DoesNotExist:
    #         return self.send_response(
    #             success=False,
    #             code='422',
    #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #             description='Symptom Does`t Exist'
    #         )
    #
    #     except Exception as e:
    #
    #         return self.send_response(
    #             success=False,
    #             description=e
    #         )


class DeleteAppointmentView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def get(self, request, pk=None):
        try:

            Appointment.objects.get(id=pk, user_id=request.user.id).delete()
            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                description='Appointment Deleted Successfully'

            )


        except Appointment.DoesNotExist:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code='422',
                description='Invalid Appointment id'
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )


class CalendarView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            # category_id = request.query_params.get('category-id', None)
            # search = request.query_params.get('search', None)
            # publish = request.query_params.get('publish', None)
            # out_stock = request.query_params.get('out-of-stock', None)
            # low_thresh = request.query_params.get('low-thresh', None)
            # is_active = request.query_params.get('is-active', None)
            #  drop-dow params shows only parent products
            # listing = request.query_params.get('drop-down', None)

            query_set = Q(user_id=request.user.id)

            # if pk:
            #     query_set &= Q(id=pk)
            #     query = Appointment.objects.get(query_set)
            #     serializer = AppointmentSerializer(query)
            #     count = 1
            # else:
            query = Event.objects.prefetch_related(
                Prefetch("event_appointment", queryset=Appointment.objects.all().order_by('date'),
                         to_attr='appointment'),
                Prefetch("event_symptoms", queryset=Symptoms.objects.all().order_by('date'),
                         to_attr='symptoms'),

                Prefetch("event_medicine", queryset=EventMedication.objects.prefetch_related(
                    Prefetch(
                        "medicine__medicine_dosage",
                        queryset=DosageTime.objects.filter(is_active=True)
                    )).filter(is_active=True),
                         to_attr='medicine'),
            ).filter(query_set)

            serializer = EventSerializer(query, many=True)
            count = 1
            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                payload=serializer.data,
                count=count
            )
        except User.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description='Appointment Does`t Exist'
            )
        except FieldError as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=f'422',
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=e
            )


class CalenderSynchronizationView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def post(self, request, pk=None):
        try:
            obj = GoogleCalenderManager(key=request.data["token"])

            x = Appointment.get_un_sync_appointment(request.user.id)
            y = DosageTime.get_un_sync_dosage(request.user.id)
            z = Symptoms.get_un_sync_appointment(request.user.id)
            appoint, dos, sym = [], [], []
            if x:
                for c, d in x.items():
                    id = obj.creat_event(d)
                    appoint.append(Appointment(id=c, event_id=id))
                Appointment.objects.bulk_update(appoint, fields=["event_id"])

            if y:
                for j, k in y.items():
                    s = ""
                    for a in k:
                        s += f'{str(obj.creat_event(a))},'
                    dos.append(DosageTime(id=j, event_id=s))
                DosageTime.objects.bulk_update(dos, fields=["event_id"])

            if z:
                for x, y in z.items():
                    id = obj.creat_event(y)
                    sym.append(Symptoms(id=x, event_id=id))

                Symptoms.objects.bulk_update(sym, fields=["event_id"])

            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                description='Calender Sync Successfully'

            )


        except Appointment.DoesNotExist:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code='422',
                description='Invalid Appointment id'
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=str(e)
            )
