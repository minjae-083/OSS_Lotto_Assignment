import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_is_public(client):
    response = client.get(reverse("lotto:home"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_anonymous_user_redirected_from_buy(client):
    response = client.get(reverse("lotto:buy"))
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_anonymous_user_redirected_from_my_tickets(client):
    response = client.get(reverse("lotto:my_tickets"))
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["admin_panel:sales", "admin_panel:draw", "admin_panel:winners"])
def test_non_staff_redirected_from_admin_pages(client, user, url_name):
    client.force_login(user)
    response = client.get(reverse(url_name))
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["admin_panel:sales", "admin_panel:draw", "admin_panel:winners"])
def test_staff_can_access_admin_pages(client, staff_user, url_name):
    client.force_login(staff_user)
    response = client.get(reverse(url_name))
    assert response.status_code == 200


@pytest.mark.django_db
def test_signup_creates_user_with_bonus_balance(client):
    response = client.post(reverse("accounts:signup"), {
        "username": "newbie",
        "password1": "ComplexPass1234!",
        "password2": "ComplexPass1234!",
    })
    assert response.status_code == 302

    from accounts.models import User
    user = User.objects.get(username="newbie")
    assert user.balance == 10000
