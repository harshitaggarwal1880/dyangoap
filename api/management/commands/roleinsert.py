from django.core.management.base import BaseCommand
from django.db import connection


from api.users.models import Role


class Command(BaseCommand):
    help = "Creating model objects according the file path specified"

    def handle(self, *args, **options):
        roles = [
            {
                "name":"Super Admin",
                "code":"super-admin",
                "access_level":900
            },
            {
                "name":"Customer",
                "code":"customer",
                "access_level":500
            }
        ]
        for item in roles:
            if not Role.objects.filter(name=item["name"]).exists():
                Role.objects.create(name=item["name"],code=item["code"],access_level=item["access_level"])
