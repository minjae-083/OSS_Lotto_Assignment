import pytest
from django.urls import reverse

from accounts.models import User
from lotto.models import Ticket
from lotto.services import create_next_draw, run_draw


@pytest.mark.django_db
def test_full_user_flow_signup_buy_auto_draw_check(client):
    # 1) 회원가입 (자동 로그인까지)
    client.post(reverse("accounts:signup"), {
        "username": "alice",
        "password1": "ComplexPass1234!",
        "password2": "ComplexPass1234!",
    })
    user = User.objects.get(username="alice")
    assert user.balance == 10000

    # 2) 관리자(시스템)가 회차 개설
    draw = create_next_draw()

    # 3) 자동 구매
    response = client.post(reverse("lotto:buy"), {"pick_type": "AUTO"})
    assert response.status_code == 302

    ticket = Ticket.objects.get(user=user)
    user.refresh_from_db()
    assert user.balance == 9000

    # 4) 추첨 실행
    drawn, _ = run_draw(draw.round_no)
    assert drawn.status == "CLOSED"

    # 5) 사용자가 결과 확인
    response = client.get(reverse("lotto:check", args=[ticket.id]))
    assert response.status_code == 200

    ticket.refresh_from_db()
    assert ticket.rank is not None
