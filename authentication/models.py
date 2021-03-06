import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models

from core.models import TimestampedModel


class UserManager(BaseUserManager):
    """
    Django requires that custom users define their own Manager class.
    """

    def create_user(self, credentials):
        """Create and return a `User` with an email, username and password."""
        if credentials['username'] is None:
            raise TypeError('Users must have a username.')

        if credentials['email'] is None:
            raise TypeError('Users must have an email address.')
        user = self.model(username=credentials['username'], email=self.normalize_email(credentials['email']))
        user.set_password(credentials['password'])
        user.first_name = credentials.get('first_name', None)
        user.last_name = credentials.get('last_name', None)
        user.city = credentials.get('city', None)
        user.state = credentials.get('state', None)
        user.country = credentials.get('country', None)
        user.save()

        return user

    def create_superuser(self, credentials):
        """
        Create and return a `User` with superuser (admin) permissions.
        """
        if credentials['password'] is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(credentials)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    email = models.EmailField(db_index=True, unique=True)
    is_active = models.BooleanField(default=False)

    # The `is_staff` flag is expected by Django to determine who can and cannot
    # log into the Django admin site.
    is_staff = models.NullBooleanField(default=False)
    is_superuser = models.NullBooleanField(default=False)

    first_name = models.CharField(max_length=20, null=True, blank=True)
    last_name = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)

    # If a user is an official page or not
    official_page = models.NullBooleanField(default=False, null=True)

    # The `USERNAME_FIELD` property tells us which field we will use to log in.
    # In this case we want it to be the username field.
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        """
        Returns a string representation of this `User`.

        This string is used when a `User` is printed in the console.
        """
        return str(self.email)

    @property
    def token(self):
        """
        Allows us to get a user's token by calling `user.token` instead of
        `user.generate_jwt_token().

        The `@property` decorator above makes this possible. `token` is called
        a "dynamic property".
        """
        return self._generate_jwt_token()

    def get_full_name(self):
        """
        This method is required by Django for things like handling emails.
        Typically this would be the user's first and last name. Since we do
        not store the user's real name, we return their username instead.
        """
        return str(self.first_name) + ' ' + str(self.last_name)

    def get_short_name(self):
        """
        This method is required by Django for things like handling emails.
        Typically, this would be the user's first name. Since we do not store
        the user's real name, we return their username instead.
        """
        return str(self.first_name)

    def _generate_jwt_token(self):
        """
        Generates a JSON Web Token that stores this user's ID and has an expiry
        date set to 60 days into the future.
        """
        dt = datetime.now() + timedelta(days=60)
        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.timestamp())
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')
