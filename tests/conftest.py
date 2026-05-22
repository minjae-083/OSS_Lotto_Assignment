import pytest
from django.contrib.auth import get_user_model

from lotto.models import Draw


User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass1234")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staff", password="staffpass1234", is_staff=True,
    )


@pytest.fixture
def open_draw(db):
    return Draw.objects.create(round_no=1)
