import io
import secrets
import time
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import pytz
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.db.models import Subquery, PositiveIntegerField
from django.template.loader import get_template
from django.utils import timezone
from oauth2_provider.models import AccessToken
from oauth2_provider.settings import oauth2_settings


# from sendgrid.helpers.mail import Mail
# from twilio.rest import Client


def parse_email(obj):
    return obj.replace(" ", "").lower()


def get_epoch_time(to_string=False):
    """
    return epoch time
    :param to_string: Boolean, True means convert to String
    :return:
    """
    seconds = int(time.time())
    if to_string:
        return str(seconds)
    return seconds


def slugify_name(string_):
    """
    Convert given string into slugify
    :param string_: String
    :return: String
    """
    if string_:
        slugify_str = '_'.join(string_.split(' '))
        return slugify_str
    return string_


def slugify_name_hyphne(string_):
    """
    Convert given string into slugify
    :param string_: String
    :return: String
    """
    if string_:
        slugify_str = '-'.join(string_.split(' '))
        return slugify_str.lower()
    return string_


def image_directory_path(instance, filename):
    """
    file will be uploaded to MEDIA_ROOT path
    :param instance: Image Object
    :param filename:  Filename
    :return:
    """
    epoch_time = get_epoch_time(to_string=True)
    slugify_filename = slugify_name(filename)
    file_name = f'{epoch_time}_{slugify_filename}'
    return file_name


def product_image_directory_path(instance, filename):
    """
    file will be uploaded to MEDIA_ROOT path
    :param instance: Image Object
    :param filename:  Filename
    :return:
    """
    epoch_time = get_epoch_time(to_string=True)
    # slugify_filename = slugify_name(filename)
    file_name = f'product/{epoch_time}-{slugify_name_hyphne(instance.image_name) if instance.image_name else slugify_name_hyphne(instance.image_alt)}.{filename.split(".").pop()}'
    return file_name


def product_tablet_mage_directory_path(instance, filename):
    """
    file will be uploaded to MEDIA_ROOT path
    :param instance: Image Object
    :param filename:  Filename
    :return:
    """
    epoch_time = get_epoch_time(to_string=True)
    # slugify_filename = slugify_name(filename)
    file_name = f'product/optimized/{epoch_time}-{slugify_name_hyphne(instance.image_name) if instance.image_name else slugify_name_hyphne(instance.image_alt)}.{filename.split(".").pop()}'
    return file_name


def boolean(value):
    """Parse the string ``"true"`` or ``"false"`` as a boolean (case
    insensitive). Also accepts ``"1"`` and ``"0"`` as ``True``/``False``
    (respectively). If the input is from the request JSON body, the type is
    already a native python boolean, and will be passed through without
    further parsing.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        raise ValueError("boolean type must be non-null")
    value = str(value).lower()
    if value in ('true', 'yes', '1', 1):
        return True
    if value in ('false', 'no', '0', 0, ''):
        return False
    raise ValueError("Invalid literal for boolean(): {0}".format(value))


# class ManageS3:
#     def __init__(self):
#         self.s3 = boto3.client(
#             's3',
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
#         )
#
#     def delete_s3_images(self, object_keys=[]):
#         try:
#             self.s3.delete_objects(
#                 Bucket=settings.AWS_STORAGE_BUCKET_NAME,
#                 Delete={
#                     'Objects': [{'Key': key} for key in object_keys]
#                 }
#             )
#             # return response
#             return True
#         except Exception as e:
#             return False
#
#     def rename_s3_image(self, old_keys=[], new_keys=[]):
#         try:
#             bucket = self.s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
#             for i in range(len(old_keys)):
#                 bucket.Object(new_keys[i]).copy_from(CopySource=f"{bucket.name}/{old_keys[i]}")
#                 bucket.Object(old_keys[i]).delete()
#             # return response
#             return True
#         except Exception as e:
#             return False


def flat_array_dict(array, key):
    return [x[key] for x in array]


def search_array_of_dict(array, key, value):
    return [d for d in array if d[key] == value]


def sku_creator(product_name, color, id):
    return f'SKU-{product_name[:2]}-{color[:2]}-{id}'.upper()


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SubqueryAggregate(Subquery):
    # https://code.djangoproject.com/ticket/10060
    template = '(SELECT %(function)s(_agg."%(column)s") FROM (%(subquery)s) _agg)'

    def __init__(self, queryset, column, output_field=None, **extra):
        if not output_field:
            # infer output_field from field type
            output_field = queryset.model._meta.get_field(column)
        super().__init__(queryset, output_field, column=column, function=self.function, **extra)


class SubquerySum(SubqueryAggregate):
    function = 'SUM'


# def send_email_sendgrid_template(from_email="", to_email="", subject="", data="", template=""):
#     try:
#         sg = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
#
#         message = sendgrid.helpers.mail.Mail(
#             from_email=from_email,
#             to_emails=to_email,
#             subject=subject
#         )
#         message.dynamic_template_data = data
#         message.template_id = template
#         status = sg.send(message)
#         return [status]
#     except Exception as e:
#         return e

#
# def send_SMS(from_, to_, body):
#     try:
#         client = Client(settings.TIWILO_SID, settings.TIWILO_AUTH_TOKEN)
#
#         message = client.messages.create(
#             from_=f'whatsapp:{from_}',
#             body=body,
#             to=f'whatsapp:{to_}'
#         )
#     except Exception as e:
#         return


def get_manual_access_token(user):
    access_token = AccessToken()
    access_token.user = user
    access_token.client_id = settings.OAUTH_CLIENT_ID
    access_token.token = secrets.token_urlsafe(40)
    access_token.expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    # Save the access token
    access_token.save()
    # Access token value
    return access_token.token


from django.core.mail import EmailMultiAlternatives
from django.template import Context


def send_email(send_to, from_, context, html_template, subject):
    try:
        d = Context(context)
        htmly = get_template(html_template)
        html_content = htmly.render(context)
        msg = EmailMultiAlternatives(from_email=from_,
                                     to=[send_to],
                                     subject=subject)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        return


import requests


class GoogleCalenderManager:
    def __init__(self, key):
        self.access_key = key

    def creat_event(self, obj):
        global response
        try:

            headers = {
                'Authorization': f'Bearer {self.access_key}',
                'Content-Type': 'application/json',
            }

            response = requests.post('https://www.googleapis.com/calendar/v3/calendars/primary/events', json=obj,
                                     headers=headers)
            created_event = response.json()
            return created_event["id"]

        except Exception as e:
            raise Exception(response.json())

    def delete_event(self, event_id):
        headers = {
            'Authorization': f'Bearer {self.access_key}',
            'Content-Type': 'application/json',
        }
        response = requests.delete(f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}',
                                   headers=headers)
        if response.status_code == 204:
            print('Event deleted')
        else:
            print('Failed to delete event')

    def get_events(self):
        headers = {
            'Authorization': f'Bearer {self.access_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(f'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                                headers=headers)
        return response.json()


def search_array_of_dict(array, key, value, is_month):
    for x in array:
        if is_month:
            if x[key].month == value.month:
                return x
        else:
            if x[key] == value:
                return x
    return None


def convert_to_localtime(utctime):
    fmt = "%H:%M:%S"
    utc = utctime.replace(tzinfo=pytz.UTC)
    localtz = utc.astimezone(timezone.get_current_timezone())
    return localtz.strftime(fmt)
