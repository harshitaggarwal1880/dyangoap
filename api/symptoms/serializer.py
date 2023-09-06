from rest_framework import serializers

from api.symptoms.models import Symptoms
from main.serilaizer import DynamicFieldsModelSerializer


class SymptomsSerializer(DynamicFieldsModelSerializer):
    title = serializers.CharField()
    user_id = serializers.IntegerField(read_only=True)
    description = serializers.CharField()
    severity = serializers.CharField()
    time = serializers.CharField()
    duration = serializers.CharField()
    associated_factors = serializers.CharField()
    medications_taken = serializers.CharField()
    notes = serializers.CharField()
    triggers = serializers.CharField()
    date = serializers.DateField()
    body_part = serializers.CharField()
    factor_other = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    triger_other = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Symptoms
        fields = [
            "id",
            "user_id",
            "title",
            "description",
            "severity",
            "time",
            "duration",
            "associated_factors",
            "medications_taken",
            "notes",
            "triggers",
            "date",
            "body_part",
            "factor_other",
            "triger_other"
        ]

    def create(self, validated_data):
        return Symptoms.create(validated_data)

    def update(self, instance, validated_data):
        instance.description = validated_data.get("description", instance.description)
        instance.severity = validated_data.get("severity", instance.severity)
        instance.time = validated_data.get("time", instance.time)
        instance.duration = validated_data.get("duration", instance.duration)
        instance.associated_factors = validated_data.get("associated_factors", instance.associated_factors)
        instance.medications_taken = validated_data.get("medications_taken", instance.medications_taken)
        instance.notes = validated_data.get("notes", instance.notes)
        instance.triggers = validated_data.get("triggers", instance.triggers)
        instance.factor_other = validated_data.get("factor_other", instance.factor_other)
        instance.triger_other = validated_data.get("triger_other", instance.triger_other)
        instance.save()
        return instance
