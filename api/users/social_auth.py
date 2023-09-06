import secrets
from abc import abstractmethod, ABC
from datetime import timedelta
from enum import Enum

import requests
from django.conf import settings
from django.utils import timezone
from oauth2_provider.models import AccessToken
from oauth2_provider.settings import oauth2_settings

from api.users.models import User, Role
from api.users.serializer import UserSerializer


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


class SocialPlatform(Enum):
    FACEBOOK = 'facebook'
    GOOGLE = 'google'


"""Abstract Class"""


class SocialAuthentication(ABC):
    def __init__(self, access_token):
        self.access_token = access_token

    @abstractmethod
    def get_or_create_user(self):
        pass

    def authenticate(self):
        user = self.get_or_create_user()
        if user:
            token = get_manual_access_token(user)
            user_data = UserSerializer(user).data
            user_data['access_token'] = token
            return user_data
        raise ValueError("Invalid Access Key")


class FaceBookAuth(SocialAuthentication):
    def __init__(self, access_token):
        super().__init__(access_token)
        self._base_url = 'https://graph.facebook.com/'

    def get_or_create_user(self):
        try:
            response = requests.post(
                url=self._base_url + f'me?fields=id,name,email&access_token={self.access_token}',
                headers={
                    'Authorization': 'Bearer' + self.access_token
                },
            )
            if response.ok:
                facebook_id = response.json()["id"]
                email = response.json()["email"]
                first_name, last_name = response.json()["name"].split()[0:2]
                user, is_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "role": Role.objects.get(code__exact='customer'),
                        "is_active": True,
                        "first_name": first_name,
                        "last_name": last_name,
                        "facebook_id": facebook_id
                    }
                )
                return user

            else:
                return None
        except Exception as e:
            raise e


class GoogleAuth(SocialAuthentication):
    def __init__(self, access_token):
        super().__init__(access_token)
        self._base_url = 'https://people.googleapis.com/v1/people/me?personFields=names,genders,emailAddresses,phoneNumbers'

    def get_or_create_user(self):
        try:
            response = requests.get(
                url=self._base_url,
                headers={'Authorization': 'Bearer ' + self.access_token},
            )
            if response.ok:
                google_id = response.json()["resourceName"].split('people/')[1]
                email = response.json()["emailAddresses"][0]["value"]
                first_name, last_name = response.json()["names"][0]["displayName"].split()[0:2]
                user, is_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": Role.objects.get(code__exact='customer'),
                        "is_active": True,
                        "google_id": google_id
                    }
                )
                return user
            else:
                raise ValueError({"error": response.json()["error"]["message"]})
        except Exception as e:
            raise ValueError(str(e))


class SocialAuthContext:
    def __init__(self, social_id, platform: SocialPlatform):
        self.access_token = social_id
        self.platform = platform


class SocialAuthFactory:
    @staticmethod
    def create_social_auth(context: SocialAuthContext):
        if context.platform == SocialPlatform.GOOGLE.value:
            return GoogleAuth(context.access_token)

        if context.platform == SocialPlatform.FACEBOOK.value:
            return FaceBookAuth(context.access_token)
