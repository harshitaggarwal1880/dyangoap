from rest_framework import serializers

from api.calendars.models import Appointment, Event
from api.medicine.models import EventMedication
from api.medicine.serializer import MedicineSerializer, EventMedicineSerializer
from api.symptoms.serializer import SymptomsSerializer
from api.users.models import User
from medication.utils import convert_to_localtime


class AppointmentSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    location = serializers.CharField()
    date = serializers.DateTimeField()
    remainder = serializers.IntegerField()

    class Meta:
        model = Appointment
        fields = (
            "user_id",
            "id",
            "title",
            "location",
            "date",
            "remainder",
        )

    def create(self, validated_data):
        return Appointment.create(validated_data)

    def to_representation(self, instance):
        data = super(AppointmentSerializer, self).to_representation(instance)
        data['time'] = convert_to_localtime(instance.date)
        return data


class EventSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True, many=True)
    symptoms = SymptomsSerializer(read_only=True, many=True)
    medicine = EventMedicineSerializer(read_only=True, many=True)

    class Meta:
        model = Event
        fields = ("date", "appointment", "symptoms", "medicine")
