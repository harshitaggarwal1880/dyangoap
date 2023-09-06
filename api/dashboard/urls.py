from django.urls import path

from api.dashboard.views import DashboardView

urlpatterns = [
    path('', DashboardView.as_view())
]
