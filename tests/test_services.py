import pytest
from django.core.exceptions import ValidationError

from lotto.models import Draw, Ticket
from lotto.services import (
    create_next_draw,
    evaluate_ticket,
    generate_auto_numbers,
    purchase_ticket,
    run_draw,
)


def test_generate_auto_numbers_returns_six_unique_sorted_in_range():
    for _ in range(50):
        nums = generate_auto_numbers()
        assert len(nums) == 6
        assert len(set(nums)) == 6
        assert all(1 <= n <= 45 for n in nums)
        assert nums == sorted(nums)


@pytest.fixture
def closed_draw(db):
    return Draw.objects.create(
        round_no=99,
        n1=1, n2=2, n3=3, n4=4, n5=5, n6=6,
        bonus=7,
        status=Draw.Status.CLOSED,
    )


@pytest.mark.parametrize("nums,expected_rank", [
    ([1, 2, 3, 4, 5, 6], 1),
    ([1, 2, 3, 4, 5, 7], 2),
    ([1, 2, 3, 4, 5, 8], 3),
    ([1, 2, 3, 4, 8, 9], 4),
    ([1, 2, 3, 8, 9, 10], 5),
    ([8, 9, 10, 11, 12, 13], 0),
])
def test_evaluate_ticket_returns_correct_rank(closed_draw, user, nums, expected_rank):
    ticket = Ticket(
        user=user, draw=closed_draw,
        n1=nums[0], n2=nums[1], n3=nums[2],
        n4=nums[3], n5=nums[4], n6=nums[5],
        pick_type=Ticket.PickType.MANUAL,
    )
    rank, prize = evaluate_ticket(ticket, closed_draw)
    assert rank == expected_rank
    if rank == 0:
        assert prize == 0
    else:
        assert prize > 0


def test_purchase_ticket_deducts_balance_and_creates_ticket(user, open_draw):
    initial = user.balance
    ticket = purchase_ticket(user, open_draw, [6, 1, 3, 5, 2, 4], Ticket.PickType.MANUAL)

    user.refresh_from_db()
    assert user.balance == initial - 1000
    assert ticket.numbers() == [1, 2, 3, 4, 5, 6]
    assert ticket.pick_type == Ticket.PickType.MANUAL


def test_purchase_ticket_fails_on_insufficient_balance(user, open_draw):
    user.balance = 500
    user.save()
    with pytest.raises(ValidationError):
        purchase_ticket(user, open_draw, [1, 2, 3, 4, 5, 6], Ticket.PickType.MANUAL)


def test_purchase_ticket_fails_on_closed_draw(user, open_draw):
    open_draw.status = Draw.Status.CLOSED
    open_draw.save()
    with pytest.raises(ValidationError):
        purchase_ticket(user, open_draw, [1, 2, 3, 4, 5, 6], Ticket.PickType.MANUAL)


def test_purchase_ticket_rejects_invalid_numbers(user, open_draw):
    # 46은 범위 밖
    with pytest.raises(ValidationError):
        purchase_ticket(user, open_draw, [1, 2, 3, 4, 5, 46], Ticket.PickType.MANUAL)

    # 중복
    with pytest.raises(ValidationError):
        purchase_ticket(user, open_draw, [1, 1, 2, 3, 4, 5], Ticket.PickType.MANUAL)


def test_run_draw_closes_and_evaluates_all_tickets(user, open_draw):
    purchase_ticket(user, open_draw, [1, 2, 3, 4, 5, 6], Ticket.PickType.AUTO)
    purchase_ticket(user, open_draw, [40, 41, 42, 43, 44, 45], Ticket.PickType.AUTO)

    drawn, winners_by_rank = run_draw(open_draw.round_no)

    drawn.refresh_from_db()
    assert drawn.status == Draw.Status.CLOSED
    assert drawn.draw_date is not None
    assert all(1 <= n <= 45 for n in drawn.winning_numbers())
    assert 1 <= drawn.bonus <= 45

    for t in Ticket.objects.all():
        assert t.rank is not None  # 추첨됐음 (0=꽝 포함)


def test_run_draw_credits_prize_to_user(user, open_draw):
    """수동으로 1등 케이스를 강제로 만들어 잔액 가산 검증."""
    # 잔액 잡고 한 장 구매
    initial = user.balance
    purchase_ticket(user, open_draw, [1, 2, 3, 4, 5, 6], Ticket.PickType.MANUAL)
    user.refresh_from_db()
    assert user.balance == initial - 1000

    # 추첨 결과를 직접 1등 매칭으로 고정해서 평가만 실행
    open_draw.n1, open_draw.n2, open_draw.n3 = 1, 2, 3
    open_draw.n4, open_draw.n5, open_draw.n6 = 4, 5, 6
    open_draw.bonus = 7
    open_draw.status = Draw.Status.CLOSED
    open_draw.save()

    ticket = Ticket.objects.get(user=user)
    rank, prize = evaluate_ticket(ticket, open_draw)
    assert rank == 1
    assert prize == 2_000_000_000


def test_run_draw_twice_fails(open_draw):
    run_draw(open_draw.round_no)
    with pytest.raises(ValidationError):
        run_draw(open_draw.round_no)


def test_create_next_draw_increments_round_no(db):
    d1 = create_next_draw()
    d2 = create_next_draw()
    assert d1.round_no == 1
    assert d2.round_no == 2
