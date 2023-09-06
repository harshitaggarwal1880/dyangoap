from django.urls import path

from api.medicine.views import MedicineView, DeleteMedicineView, DoseIntakeView, ImageUploadView

urlpatterns = [
    path("", MedicineView.as_view()),
    path("<int:pk>", MedicineView.as_view()),
    path("delete/<int:pk>", DeleteMedicineView.as_view()),
    path("dose-intake/<int:pk>", DoseIntakeView.as_view()),
    path("image", ImageUploadView.as_view()),
]
