from django.contrib.auth import authenticate
from oauth2_provider.models import AccessToken
from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler

from api.users.models import AccessLevel


class BaseAuthPermission(permissions.BasePermission):

    def verify_header(self, request):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    request.user = request._cached_user = user
                    # request.data['created_by'] = request.user.id
                    return True
        return False

    def verify_cookie(self, request):
        try:
            access_token = request.COOKIES.get('u-at', None)
            if access_token:
                request.user = AccessToken.objects.get(token=access_token).user
                request.user.access_token = access_token
                # request.data['created_by'] = request.user.id
                return True
            else:
                return False
        except AccessToken.DoesNotExist:
            return False


class IsAuthenticated(BaseAuthPermission):

    def has_permission(self, request, view):
        # allow all POST requests

        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    request.user = request._cached_user = user
                    return True
                return False
        return False


class IsOauthAuthenticatedSuperAdminAndCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code in [AccessLevel.SUPER_ADMIN_CODE, AccessLevel.CUSTOMER_CODE,
                                          AccessLevel.MEMBER_CODE]:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsOauthAuthenticatedSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.SUPER_ADMIN_CODE:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class GETIsOauthAuthenticatedSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.SUPER_ADMIN_CODE:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsOauthAuthenticatedCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code in [AccessLevel.CUSTOMER_CODE]:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsGetOrAuthenticatedSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "GET":
            request.user = authenticate(request=request)
            return True
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.SUPER_ADMIN_CODE:
                        request.user = request._cached_user = user
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


def custom_exception_handler(exc, context):
    if isinstance(exc, NotAuthenticated):
        return Response({"description": "Authentication credentials were not provided."},
                        status=401)

    # else
    # default case
    return exception_handler(exc, context)


class IsAuthenticatedOrAllow(BaseAuthPermission):

    def has_permission(self, request, view):
        # allow all POST requests

        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    request.user = request._cached_user = user
                    return True
                return True
        return True


class IsOauthAuthenticatedSuperAdminAndMember(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code in [AccessLevel.SUPER_ADMIN_CODE, AccessLevel.MEMBER_CODE]:
                        if user.role.code == AccessLevel.MEMBER_CODE and not user.is_approved:
                            return False

                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsMemberGetOrOauthAuthenticatedSuperAdmin(permissions.BasePermission):
    message = 'Authentication credentials were not provided'

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.SUPER_ADMIN_CODE or user.role.code == AccessLevel.MEMBER_CODE and request.method == 'GET':
                        # if user.role.code == AccessLevel.MEMBER_CODE and not user.is_approved:
                        #     return False
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True
                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsOauthAuthenticatedMember(permissions.BasePermission):
    message = 'Authentication credentials were not provided.'

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code == AccessLevel.MEMBER_CODE:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True

                    else:
                        return False
        else:
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False


class IsGetOrOauthAuthenticatedCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get("HTTP_AUTHORIZATION", "").startswith("Bearer"):
            if not hasattr(request, "user") or request.user.is_anonymous:
                user = authenticate(request=request)
                if user:
                    if user.role.code in [AccessLevel.MEMBER_CODE,
                                          AccessLevel.CUSTOMER_CODE]:
                        request.user = request._cached_user = user
                        # request.data['created_by'] = request.user.id
                        return True

                    else:
                        return False
        else:
            if request.method == 'GET':
                return True
            try:
                access_token = request.COOKIES.get('u-at', None)
                if access_token:
                    request.user = AccessToken.objects.get(token=access_token).user
                    request.user.access_token = access_token
                    request.data['created_by'] = request.user.id
                    return True
                else:
                    return False
            except AccessToken.DoesNotExist:
                return False
