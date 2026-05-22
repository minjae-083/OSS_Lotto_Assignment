from django.contrib.auth.models import AbstractUser
from django.db import models


SIGNUP_BONUS = 10000


class User(AbstractUser):
    balance = models.PositiveIntegerField(default=SIGNUP_BONUS)

    def __str__(self):
        return self.username
