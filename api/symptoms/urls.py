from django.urls import path

from api.symptoms.views import SymptomsView, DeleteSymptomsView

urlpatterns = [
    path("", SymptomsView.as_view()),
    path("<int:pk>", SymptomsView.as_view()),
    path("delete/<int:pk>", DeleteSymptomsView.as_view())
]
