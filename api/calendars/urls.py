from django.urls import path

from api.calendars.views import AppointmentView, DeleteAppointmentView, CalendarView, CalenderSynchronizationView

urlpatterns = [
    path("", CalendarView.as_view()),
    path("appointment", AppointmentView.as_view()),
    path('appointment/delete/<int:pk>', DeleteAppointmentView.as_view()),
    path("sync", CalenderSynchronizationView.as_view())
]
