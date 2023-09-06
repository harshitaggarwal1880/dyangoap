from django.db import models

# Create your models here.
import random
from datetime import datetime, timedelta
from uuid import uuid4

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import IntegrityError
from django.db import models, transaction
# Create your models here.
from django.db.models import Sum
from django.db.models.functions import Coalesce

# Create your models here.
from django.template.defaultfilters import slugify

from main.models import Log
from medication.utils import parse_email


class AccessLevel:
    """
    Access levels for user roles.
    """
    CUSTOMER = 500
    # OPERATOR = 600
    # MEMBER = 800
    SUPER_ADMIN = 900

    CUSTOMER_CODE = 'customer'
    # OPERATOR_CODE = 'operator'
    # MEMBER_CODE = 'member'
    SUPER_ADMIN_CODE = 'super-admin'

    CHOICES = (
        (CUSTOMER, "Customer"),
        (SUPER_ADMIN, 'Super Admin'),
        # (OPERATOR, 'Operator'),
        # (MEMBER, 'Member')
    )

    CODES = (
        (CUSTOMER, "customer"),
        (SUPER_ADMIN, 'super-admin'),
        # (OPERATOR, 'operator'),
        # (MEMBER, 'member')
    )
    DICT = dict(CHOICES)
    CODES_DICT = dict(CODES)


class Role(Log):
    """ Role model."""
    name = models.CharField(db_column='Name', max_length=255, unique=True)
    code = models.SlugField(db_column='Code', default='')
    description = models.TextField(db_column='Description', null=True, blank=True)
    access_level = models.IntegerField(db_column='AccessLevel', choices=AccessLevel.CHOICES,
                                       default=AccessLevel.CUSTOMER)

    class Meta:
        db_table = 'Roles'

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.code = slugify(self.name)
            super().save()
        except Exception:
            raise

    @staticmethod
    def get_role_by_code(code=None):
        try:
            return Role.objects.get(code__exact=code)
        except Exception as e:
            print(e)
            return e


class CustomAccountManager(BaseUserManager):

    def create_user(self, email, password):
        user = self.model(email=email, password=password)
        passw = password
        user.set_password(passw)
        user.is_superuser = False
        user.is_approved = False
        user.is_active = False
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password)
        passw = password
        user.set_password(passw)
        user.is_superuser = True
        user.is_approved = True
        user.is_active = True
        # user.user_roles.create()
        user.role = Role.objects.get(code=AccessLevel.SUPER_ADMIN_CODE)
        # Group.objects.get_or_create(name='Super_Admin')
        # user.groups.add(Super_Admin)
        user.save()
        return user


class User(AbstractBaseUser, Log, PermissionsMixin):
    """ User model."""
    first_name = models.TextField(db_column='FirstName', default="")
    # middle_name = models.TextField(db_column='MiddleName', default="")
    last_name = models.TextField(db_column='LastName', default="")
    approved_by_user = models.IntegerField(db_column='ApprovedByUser', default=0)
    is_active = models.BooleanField(
        db_column='IsActive',
        default=False,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.',
    )
    is_approved = models.BooleanField(
        db_column='IsApproved',
        default=False,
        help_text='Designates whether this user is approved or not.',
    )
    email = models.EmailField(unique=True, db_column="Email", help_text="Email Field", null=True)
    is_email_verified = models.BooleanField(db_column='IsEmailVerified', default=False)
    role = models.ForeignKey(Role, db_column='RoleId', related_name='user_role', on_delete=models.CASCADE, default="",
                             null=True, blank=True)
    is_staff = models.BooleanField(
        default=True,
        help_text='Designates whether the user can log into this admin site.',
    )

    is_deleted = models.BooleanField(
        default=False,
        db_column='IsDeleted'
    )
    # search_vector = SearchVectorField(null=True)
    # image = models.ImageField(upload_to=image_directory_path, null=True)
    # bio = models.TextField(db_column='Bio', null=True)
    # no_visiting = models.IntegerField(default=0)
    objects = CustomAccountManager()
    # objects = UserSearchManager()
    date_of_birth = models.DateField(db_column='DateOfBirth', null=True)
    blood_group = models.CharField(max_length=255, null=True)
    allergies = models.CharField(max_length=255, null=True)
    emergency_contact = models.CharField(max_length=255, null=True)
    medical_condition = models.CharField(max_length=255, null=True)
    medical_id = models.CharField(max_length=255, null=True)
    # access_token = models.TextField(null=True)
    image = models.ImageField(null=True)
    google_id = models.TextField(null=True)
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    # REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = 'Users'

    # def update_member(self, validated_data):
    #     self.first_name = validated_data.get("first_name", self.first_name)
    #     self.last_name = validated_data.get("last_name", self.last_name)
    #     self.date_of_birth = validated_data.get("date_of_birth", self.date_of_birth)
    #     self.gender = validated_data.get("gender", self.gender)
    #     self.phone = validated_data.get("phone", self.phone)
    #     self.city = validated_data.get("city", self.city)
    #     self.ibn = validated_data.get("ibn", self.ibn)
    #     self.cnic = validated_data.get("cnic", self.cnic)
    #     self.ntn = validated_data.get("ntn", self.ntn)
    #     self.role_id = validated_data.get("role_id", self.role_id)

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.medical_id = random.randint(10000, 999999)

                if self.email:
                    self.email = parse_email(self.email)
            super().save()
        except Exception:
            raise

    # def add_members_points(self, points, order_id):
    #     self.member_points.create(
    #         points=points,
    #         order_id=order_id
    #     )


# class UserRole(Log):
#     user = models.ForeignKey(
#         User,
#         db_column='UserId',
#         related_name='user_roles',
#         on_delete=models.CASCADE
#     )
#     role = models.ForeignKey(
#         Role,
#         db_column='RoleID',
#         related_name='role_users',
#         on_delete=models.CASCADE
#     )
#     is_active = models.BooleanField(db_column='IsActive', default=True)
#
#     class Meta:
#         db_table = "Pro_Wears_Users_Roles"


class EmailVerificationLink(Log):
    token = models.CharField(db_column='Token', primary_key=True, unique=True, max_length=255)
    code = models.IntegerField(db_column="Code", null=True, blank=True, default=None)
    user = models.ForeignKey(User, db_column='UserId', related_name='user_id', on_delete=models.CASCADE)
    expiry_at = models.DateTimeField(db_column='ExpireAt')

    class Meta:
        db_table = "Trainee_Email_Verification"

    def save(self, *args, **kwargs):
        try:
            if not self.pk:
                self.token = uuid4()
                self.code = random.randint(1000, 9999)
            super().save()
        except Exception:
            raise

    @staticmethod
    def add_email_token_link(user):
        try:
            object = {"user": user, "expiry_at": datetime.now() + timedelta(+5)}
            email_link = EmailVerificationLink.objects.create(**object)
            print(email_link)

            # send_email_sendgrid_template(
            #     from_email=settings.CONTACT_US_EMAIL,
            #     to_email=user.email,
            #     subject="Forgot Password",
            #     data=data,
            #     template=settings.FORGOT_PASSWORD_TEMPLATE_ID
            # )
            return email_link
        except Exception as e:
            return e
