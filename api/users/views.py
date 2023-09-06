from django.shortcuts import render

# Create your views here.
from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate, logout, get_user_model
from django.core.exceptions import FieldError
# Create your views here.
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.views import TokenView
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from api.permissions import IsOauthAuthenticatedSuperAdminAndCustomer, IsOauthAuthenticatedSuperAdmin, \
    IsOauthAuthenticatedCustomer, IsAuthenticated
from api.users.models import User, EmailVerificationLink, AccessLevel
from api.users.serializer import AuthenticateSerializer, UserSerializer, SignUpSerializer, SocialAuthenticateSerializer
from api.users.social_auth import SocialAuthFactory, SocialAuthContext

from api.views import BaseAPIView
from medication.utils import parse_email, boolean, send_email


class SignUpView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            serializer = SignUpSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                oauth_token = self.get_oauth_token(parse_email(request.data['email']), request.data['password'])
                if 'access_token' in oauth_token:
                    user_data = serializer.data
                    user_data['access_token'] = oauth_token.get('access_token')
                    user_data['refresh_token'] = oauth_token.get('refresh_token')
                    return self.send_response(
                        success=True,
                        code=f'201',
                        status_code=status.HTTP_201_CREATED,
                        payload=user_data,
                        description="Customer Created Successfully",
                    )
            else:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="Invalid form data",
                    exception=serializer.errors,
                )

        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class UserProfileUpdateView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def get(self, request, pk=None):
        try:
            query = User.objects.get(id=request.user.id)
            serializer = UserSerializer(query)
            return self.send_response(
                success=True,
                status_code=status.HTTP_200_OK,
                payload=serializer.data
            )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )

    def put(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            user_data = User.objects.get(id=request.user.id)
            # user = User
            serializer = UserSerializer(
                instance=user_data,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return self.send_response(
                    success=True,
                    code=f'200',
                    status_code=status.HTTP_200_OK,
                    payload=UserSerializer(serializer.instance).data,
                    description="User Updated Successfully",
                )
            else:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors,
                )

        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class UserProfilePasswordView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            user_data = User.objects.get(id=request.user.id)
            if not request.data['new_password']:
                return self.send_response(
                    success=True,
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="Password Required",
                )
            else:
                if user_data.check_password(request.data['old_password']):
                    user_data.set_password(request.data['new_password'])
                    user_data.save()
                    # user = User
                    return self.send_response(
                        success=True,
                        code=f'200',
                        status_code=status.HTTP_200_OK,
                        description="Password Updated Successfully",
                    )
                else:
                    return self.send_response(
                        success=True,
                        code=f'422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        description="Invalid Password",
                    )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User doesn't exist"
            )
        except FieldError:
            return self.send_response(
                code=f'500',
                description="Cannot resolve keyword given in 'order_by' into field"
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class LoginView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        try:
            serializer = AuthenticateSerializer(data=request.data)
            if serializer.is_valid():
                email = parse_email(serializer.data.get('email'))
                password = serializer.data.get('password')
                user = authenticate(request, email=email, password=password)
                if user:

                    if user.is_active:

                        oauth_token = self.get_oauth_token(email, password)
                        if 'access_token' in oauth_token:
                            # user_data = {'access_token': oauth_token.get('access_token'),
                            #              'refresh_token': oauth_token.get('refresh_token')}
                            serialized = UserSerializer(User.objects.get(id=user.id))
                            user_data = serialized.data
                            user_data['access_token'] = oauth_token.get('access_token')
                            user_data['refresh_token'] = oauth_token.get('refresh_token')
                            return self.send_response(success=True,
                                                      code=f'200',
                                                      status_code=status.HTTP_200_OK,
                                                      payload=user_data,
                                                      description='You are logged in!',
                                                      )
                        else:
                            return self.send_response(description='Something went wrong with Oauth token generation.',
                                                      code=f'500')
                    else:
                        description = 'Your account is blocked or deleted.'
                        return self.send_response(success=False,
                                                  code=f'422',
                                                  status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                                  payload={},
                                                  description=description)
                else:
                    return self.send_response(
                        success=False,
                        code=f'422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        payload={}, description='Email or password is incorrect.'
                    )
            else:
                return self.send_response(
                    success=False,
                    code='422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )


        except Exception as e:
            return self.send_response(code=f'500',
                                      description=e)


class LogoutView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = ()

    def get(self, request):
        try:
            token = request.META.get("HTTP_AUTHORIZATION", "").replace("Bearer ", "")
            if not self.revoke_oauth_token(token):
                return self.send_response(code=f'422',
                                          status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                          description="User doesn't logout")
            logout(request)
            return self.send_response(success=True,
                                      code=f'201', status_code=status.HTTP_201_CREATED,
                                      payload={},
                                      description='User logout successfully'
                                      )
        except User.DoesNotExist:
            return self.send_response(code=f'422',
                                      status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                      description="User doesn't exists")
        except FieldError:
            return self.send_response(code=f'500',
                                      description="Cannot resolve keyword given in 'order_by' into field")
        except Exception as e:
            return self.send_response(code=f'500',
                                      description=e)


# class VerifyInvitationLink(BaseAPIView):
#     """
#     Verify the Link of the Local Admin
#     """
#     authentication_classes = ()
#     permission_classes = ()
#
#     def post(self, request, pk=None):
#         """
#         In this API, we will validate the **Local Admin** token. Whether it is a valid token, or unexpired.
#         If it is, it will return the user_id using which **Local Admin** will update his/her password
#         """
#         try:
#             verify = EmailVerificationLink.objects.get(token=request.data['token'], code=request.data['code'])
#             if datetime.date(verify.expiry_at) <= datetime.date(datetime.now()):
#                 EmailVerificationLink.add_email_token_link(verify.user)
#                 verify.delete()
#                 return self.send_response(
#                     code=f'422',
#                     status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                     description="The link is expired. New link has been sent to your email"
#                 )
#             else:
#                 return self.send_response(
#                     success=True,
#                     code=f'201',
#                     status_code=status.HTTP_201_CREATED,
#                     payload={"user_id": verify.user_id},
#                     description="Token Verified Successfully"
#                 )
#         except EmailVerificationLink.DoesNotExist:
#             return self.send_response(
#                 code=f'422',
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 description="Verification token doesn't exists"
#             )
#         except Exception as e:
#             return self.send_response(
#                 code=f'500',
#                 description=e
#             )


class UpdatePassword(BaseAPIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        """
        In this API, we will validate the **Local Admin** token. Whether it is a valid token, or unexpired.
        If it is, it will return the user_id using which **Local Admin** will update his/her password
        """
        try:
            verify = EmailVerificationLink.objects.get(token=request.data['token'],
                                                       )
            if datetime.date(verify.expiry_at) <= datetime.date(datetime.now()):
                EmailVerificationLink.add_email_token_link(verify.user)
                verify.delete()
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="The link is expired. New link has been sent to your email"
                )
            else:
                verify.user.set_password(request.data["password"])
                verify.user.save(update_fields=["password"])
                verify.delete()
            return self.send_response(
                success=True,
                code=f'201',
                status_code=status.HTTP_201_CREATED,
                description="Password Updated"
            )
        except EmailVerificationLink.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="Verification token doesn't exists"
            )
        except Exception as e:
            return self.send_response(
                code=f'500',
                description=e
            )


class ForgotPasswordView(BaseAPIView):
    parser_class = ()
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        try:
            if request.data['email'] == "" or None:
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="Email required"
                )
            else:
                user = User.objects.get(email__exact=parse_email(request.data['email']))
                obj = EmailVerificationLink.add_email_token_link(user)
                send_email(
                    from_=settings.EMAIL_HOST_USER,
                    send_to=user.email,
                    html_template='forgot_template.html',
                    context={"name": user.first_name,
                             "url": f'{settings.WEB_URL}reset-password/{obj.token}'},
                    subject='Forgot Password'

                )

                return self.send_response(
                    success=True,
                    code=f'201',
                    status_code=status.HTTP_201_CREATED,
                    description="Forgot Password mail sent successfully",
                )
        except User.DoesNotExist:
            return self.send_response(
                code=f'422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description="User does not exists"
            )
        except Exception as e:
            return self.send_response(
                code=f'500',
                description=e
            )


class UserView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedSuperAdmin,)

    def get(self, request, pk=None):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
            active = request.query_params.get('active', None)
            q = request.query_params.get('q', None)
            query_set = Q(role__code__in=[AccessLevel.CUSTOMER_CODE])

            if q:
                query_set &= Q(first_name__icontains=q) | \
                             Q(last_name__icontains=q) | \
                             Q(email__icontains=q)
            if active:
                query_set &= Q(is_active=boolean(active))
            if pk:
                query_set &= Q(id=pk)
                query = User.objects.get(query_set)
                serializer = UserSerializer(query)
                count = 1
            else:
                query = User.objects.filter(
                    query_set
                ).order_by('-id')
                serializer = UserSerializer(
                    query[offset:limit + offset],
                    many=True,
                )

                count = query.count()
            return self.send_response(
                success=True,
                code='200',
                status_code=status.HTTP_200_OK,
                payload=serializer.data,
                count=count
            )
        except User.DoesNotExist:
            return self.send_response(
                success=False,
                code='422',
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description='User Does`t Exist'
            )
        except FieldError as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=f'422',
                description=str(e)
            )

        except Exception as e:
            return self.send_response(
                success=False,
                description=e)


class CustomerUpdateProfileImageView(BaseAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOauthAuthenticatedCustomer,)

    def put(self, request, pk=None):
        """
        In this api, only **Super Admin** and **Local Admin** can login. Other users won't be able to login through this API.
        **Mandatory Fields**
        * email
        * password
        """
        try:
            request.user.image = request.data['image']
            request.user.save(update_fields=["image"])

            return self.send_response(
                success=True,
                code=status.HTTP_201_CREATED,
                payload={
                    "url": request.user.image.url
                },
                status_code=status.HTTP_201_CREATED,
                description='Profile Image Updated Successfully'
            )
            # else:
            #     return self.send_response(
            #         success=True,
            #         code=f'422',
            #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            #         description=serializer.errors,
            #     )

        # except CustomerProfile.DoesNotExist:
        #     return self.send_response(
        #         code=f'422',
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         description=_("Profile doesn't exist")
        #     )
        except FieldError:
            return self.send_response(
                code=f'500',
                description=("Cannot resolve keyword given in 'order_by' into field")
            )
        except Exception as e:
            if hasattr(e.__cause__, 'pgcode') and e.__cause__.pgcode == '23505':
                return self.send_response(
                    code=f'422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description="User with this email already exists in the system."
                )
            else:
                return self.send_response(
                    code=f'500',
                    description=e
                )


class SocialLoginView(BaseAPIView):
    """
    API View for Login Super Admin and Admin
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, pk=None):
        try:
            serializer = SocialAuthenticateSerializer(data=request.data)
            if serializer.is_valid():
                obj = SocialAuthFactory.create_social_auth(
                    context=SocialAuthContext(
                        social_id=serializer.data["token"],
                        platform=serializer.data["backend"]
                    )
                )
                if obj:
                    return self.send_response(
                        success=True,
                        status_code=status.HTTP_200_OK,
                        payload=obj.authenticate()
                    )

                else:
                    return self.send_response(
                        success=False,
                        code='422',
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        description='Invalid backend'
                    )
            else:
                return self.send_response(
                    success=False,
                    code='422',
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    description=serializer.errors
                )
        except ValueError as e:
            return self.send_response(
                success=False,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                description=str(e)

            )
        except Exception as e:
            return self.send_response(
                code=f'500',
                description=e)
