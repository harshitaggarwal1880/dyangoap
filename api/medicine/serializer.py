from datetime import date

from django.db import transaction

from api.medicine.models import DosageTime, Medicine, MedicineFrequency, Images, EventMedication
from main.serilaizer import DynamicFieldsModelSerializer
from rest_framework import serializers


class DosageTimeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    time = serializers.TimeField()
    taken = serializers.SerializerMethodField()
    day = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = DosageTime
        fields = ("id", "time", "taken", 'day')

    def get_taken(self, obj):
        return obj.is_taken()


class MedicineSerializer(DynamicFieldsModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    remainder_time = serializers.IntegerField()
    forgot_remainder = serializers.IntegerField()
    start_from = serializers.DateField()
    quantity = serializers.IntegerField()
    medicine_dosage = DosageTimeSerializer(many=True, required=True)
    total_quantity = serializers.SerializerMethodField()

    type = serializers.CharField()
    dosage_amount = serializers.IntegerField()
    unit = serializers.CharField()
    frequency = serializers.CharField()

    end_to = serializers.DateField(required=False, allow_null=True)
    meal = serializers.CharField()
    instructions = serializers.CharField()
    reminders = serializers.CharField()
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    additional_notes = serializers.CharField()
    medication_type_other = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    custom_frequency = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    days = serializers.ListField(required=False, allow_null=True, allow_empty=True)

    class Meta:
        model = Medicine
        fields = (
            "id",
            "name",
            "user_id",
            "remainder_time",
            "forgot_remainder",
            "start_from",
            "quantity",
            "medicine_dosage",
            "total_quantity",
            "end_to",
            "type",
            "dosage_amount",
            "unit",
            "frequency",
            "end_to",
            "meal",
            "instructions",
            "reminders",
            "image",
            "additional_notes",
            "medication_type_other",
            "custom_frequency",
            "days"
        )

    def create(self, validated_data):
        with transaction.atomic():
            dosage = validated_data.pop("medicine_dosage")
            obj = Medicine.objects.create(**validated_data)
            d = DosageTime.objects.bulk_create(
                [DosageTime(medicine_id=obj.id, time=x['time'], day=x.get('day', None)) for x in dosage])
            Medicine.creat_events(obj)
            return obj

    def update(self, instance, validated_data):
        with transaction.atomic():
            dosage = validated_data.pop("medicine_dosage", [])
            updated, creation, deleting = [], [], []
            for x in dosage:
                if x.get("id"):
                    deleting.append(x["id"])
                    updated.append(DosageTime(id=x["id"], time=x['time'], day=x.get('day', None)))
                else:
                    creation.append(DosageTime(medicine_id=instance.id, time=x["time"], day=x.get('day', None)))
            if updated:
                DosageTime.objects.bulk_update(updated, fields=["time", "day"])
            DosageTime.objects.filter(medicine_id=instance.id).exclude(id__in=deleting).update(is_active=False)
            if creation:
                DosageTime.objects.bulk_create(creation)

            instance.quantity = validated_data.get('quantity', instance.quantity)
            instance.name = validated_data.get('name', instance.name)
            instance.frequency = validated_data.get('frequency', instance.frequency)
            instance.remainder_time = validated_data.get('remainder_time', instance.remainder_time)
            instance.forgot_remainder = validated_data.get('forgot_remainder', instance.forgot_remainder)
            instance.start_from = validated_data.get('start_from', instance.start_from)
            instance.end_to = validated_data.get('end_to', instance.end_to)
            instance.additional_notes = validated_data.get('additional_notes', instance.additional_notes)
            instance.type = validated_data.get('type', instance.type)
            instance.medication_type_other = validated_data.get('medication_type_other', instance.medication_type_other)
            instance.reminders = validated_data.get('reminders', instance.reminders)
            instance.instructions = validated_data.get('instructions', instance.instructions)
            instance.meal = validated_data.get('meal', instance.meal)
            instance.custom_frequency = validated_data.get('custom_frequency', instance.custom_frequency)
            instance.days =validated_data.get('days', instance.days)
            EventMedication.objects.filter(medicine_id=instance.id).delete()
            EventMedication.objects.filter(medicine_id=instance.id).delete()
            Medicine.creat_events(instance)
            instance.save()
            return instance

    def get_total_quantity(self, obj):
        return obj.get_quantity()

    def to_representation(self, instance):
        data = super(MedicineSerializer, self).to_representation(instance)
        data['quantity'] = data.pop('total_quantity')
        try:
            data['image'] = instance.image.name
        except:
            return data
        return data


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=True, allow_null=False)

    class Meta:
        model = Images
        fields = ("image",)


class MedicineRemainderSerializer(DynamicFieldsModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    remainder_time = serializers.IntegerField()
    forgot_remainder = serializers.IntegerField()
    start_from = serializers.DateField()
    quantity = serializers.IntegerField()
    medicine_dosage = DosageTimeSerializer(many=True, required=True)
    email = serializers.CharField(default=None, source='user.email')
    user_name = serializers.CharField(default=None, source='user.first_name')

    total_quantity = serializers.SerializerMethodField()

    # type = serializers.CharField()
    # dosage_amount = serializers.IntegerField()
    # unit = serializers.CharField()
    # frequency = serializers.CharField()
    #
    # end_to = serializers.DateField(required=False, allow_null=True)
    # meal = serializers.CharField()
    # instructions = serializers.CharField()
    # reminders = serializers.CharField()
    # image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # additional_notes = serializers.CharField()
    # medication_type_other = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Medicine
        fields = (
            "user_id",
            "name",
            "user_id",
            "remainder_time",
            "forgot_remainder",
            "medicine_dosage",
            "start_from",
            "email",
            "user_name",
            "total_quantity",
            "quantity"

        )

    def create(self, validated_data):
        with transaction.atomic():
            dosage = validated_data.pop("medicine_dosage")
            obj = Medicine.objects.create(**validated_data)
            DosageTime.objects.bulk_create([DosageTime(medicine_id=obj.id, time=x['time']) for x in dosage])

            return obj

    def update(self, instance, validated_data):
        with transaction.atomic():
            dosage = validated_data.pop("medicine_dosage", [])
            updated, creation, deleting = [], [], []
            for x in dosage:
                if x.get("id"):
                    deleting.append(x["id"])
                    updated.append(DosageTime(id=x["id"], time=x['time']))
                else:
                    creation.append(DosageTime(medicine_id=instance.id, time=x["time"]))
            if creation:
                DosageTime.objects.bulk_create(creation)
            if updated:
                DosageTime.objects.bulk_update(updated, fields=["time"])
            if deleting:
                DosageTime.objects.filter(medicine_id=instance.id).exclude(id__in=deleting).update(is_active=False)

            instance.quantity = validated_data.get('quantity', instance.quantity)
            instance.name = validated_data.get('name', instance.name)
            instance.remainder_time = validated_data.get('remainder_time', instance.remainder_time)
            instance.forgot_remainder = validated_data.get('forgot_remainder', instance.forgot_remainder)
            instance.start_from = validated_data.get('start_from', instance.start_from)
            instance.save()
            return instance

    def get_total_quantity(self, obj):
        return obj.get_quantity()

    def to_representation(self, instance):
        data = super(MedicineRemainderSerializer, self).to_representation(instance)
        data['quantity'] = data.pop('total_quantity')
        try:
            data['image'] = instance.image.name
        except:
            return data
        return data


class EventMedicineSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)

    class Meta:
        model = EventMedication
        fields = ["medicine"]
