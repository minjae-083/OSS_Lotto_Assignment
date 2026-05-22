"""
복권 비즈니스 로직.

- generate_auto_numbers: 자동 번호 생성
- purchase_ticket: 잔액 차감 + 티켓 생성 (트랜잭션)
- run_draw: 회차 추첨 + 모든 티켓 평가 + 당첨금 지급 (트랜잭션)
- evaluate_ticket: 등수 판정
"""
import random

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from accounts.models import User

from .models import Draw, Ticket, TICKET_PRICE


# 6/45 표준 등수별 고정 상금 (실제는 동률 분배지만 본 시스템은 단순화)
PRIZE_BY_RANK = {
    1: 2_000_000_000,
    2: 50_000_000,
    3: 1_500_000,
    4: 50_000,
    5: 5_000,
}


def generate_auto_numbers():
    return sorted(random.sample(range(1, 46), 6))


def create_next_draw():
    """가장 큰 회차 다음 번호로 OPEN 상태의 회차를 생성."""
    last = Draw.objects.order_by("-round_no").first()
    next_no = (last.round_no + 1) if last else 1
    return Draw.objects.create(round_no=next_no)


def validate_numbers(numbers):
    if len(numbers) != 6:
        raise ValidationError("번호는 6개여야 합니다.")
    if len(set(numbers)) != 6:
        raise ValidationError("번호는 중복될 수 없습니다.")
    if not all(1 <= n <= 45 for n in numbers):
        raise ValidationError("번호는 1~45 사이여야 합니다.")


@transaction.atomic
def purchase_ticket(user, draw, numbers, pick_type):
    if draw.status != Draw.Status.OPEN:
        raise ValidationError("판매가 종료된 회차입니다.")

    validate_numbers(numbers)

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if locked_user.balance < TICKET_PRICE:
        raise ValidationError("잔액이 부족합니다.")

    locked_user.balance -= TICKET_PRICE
    locked_user.save(update_fields=["balance"])

    nums = sorted(numbers)
    return Ticket.objects.create(
        user=locked_user,
        draw=draw,
        n1=nums[0], n2=nums[1], n3=nums[2],
        n4=nums[3], n5=nums[4], n6=nums[5],
        pick_type=pick_type,
        price=TICKET_PRICE,
    )


def evaluate_ticket(ticket, draw):
    winning = set(draw.winning_numbers())
    picked = set(ticket.numbers())
    match = len(picked & winning)

    if match == 6:
        rank = 1
    elif match == 5 and draw.bonus in picked:
        rank = 2
    elif match == 5:
        rank = 3
    elif match == 4:
        rank = 4
    elif match == 3:
        rank = 5
    else:
        rank = 0

    return rank, PRIZE_BY_RANK.get(rank, 0)


@transaction.atomic
def run_draw(round_no):
    """OPEN 상태 회차의 추첨 실행. 당첨금은 즉시 잔액에 가산."""
    draw = Draw.objects.select_for_update().get(round_no=round_no)
    if draw.status != Draw.Status.OPEN:
        raise ValidationError("이미 추첨된 회차입니다.")

    picked = random.sample(range(1, 46), 7)
    winning = sorted(picked[:6])
    bonus = picked[6]

    draw.n1, draw.n2, draw.n3, draw.n4, draw.n5, draw.n6 = winning
    draw.bonus = bonus
    draw.status = Draw.Status.CLOSED
    draw.draw_date = timezone.now()
    draw.save()

    winners_by_rank = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for ticket in draw.tickets.select_for_update().all():
        rank, prize = evaluate_ticket(ticket, draw)
        ticket.rank = rank
        ticket.prize = prize
        ticket.save(update_fields=["rank", "prize"])
        if prize > 0:
            User.objects.filter(pk=ticket.user_id).update(
                balance=F("balance") + prize,
            )
            winners_by_rank[rank] += 1

    return draw, winners_by_rank
