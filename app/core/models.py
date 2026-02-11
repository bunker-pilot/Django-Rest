from django.db import models # noqa
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        user = self.model(email=email ,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    email = models.EmailField(unique=True, max_length=250)
    name = models.CharField(max_length=255)
    is_active=  models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
