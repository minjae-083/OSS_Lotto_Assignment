"""
시연용 시드 데이터 생성.

생성 결과:
- 1회차(CLOSED): 당첨번호 [1,2,3,4,5,6] + 보너스 7
  - alice 1등, bob 2등, carol 3등, alice 4등, bob 5등, carol 꽝
- 2회차(OPEN): 판매 중, alice/bob/carol이 수동·자동으로 구매
- 계정: admin/adminpass (staff), alice/alicepass, bob/bobpass, carol/carolpass
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from lotto.models import Draw, Ticket
from lotto.services import evaluate_ticket, generate_auto_numbers, purchase_ticket


User = get_user_model()

DEMO_USERNAMES = ["admin", "alice", "bob", "carol"]


class Command(BaseCommand):
    help = "보고서 스크린샷용 데모 데이터 생성 (1회차 추첨완료 + 2회차 판매중)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="기존 Draw/Ticket/데모 사용자 모두 삭제 후 재생성",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Ticket.objects.all().delete()
            Draw.objects.all().delete()
            User.objects.filter(username__in=DEMO_USERNAMES).delete()
            self.stdout.write(self.style.WARNING("기존 데모 데이터를 삭제했습니다."))

        if Draw.objects.exists():
            raise CommandError("이미 Draw 데이터가 있습니다. --reset 옵션을 사용하세요.")

        User.objects.create_user(
            username="admin", password="adminpass",
            is_staff=True, is_superuser=True,
        )
        alice = User.objects.create_user(username="alice", password="alicepass")
        bob = User.objects.create_user(username="bob", password="bobpass")
        carol = User.objects.create_user(username="carol", password="carolpass")

        # ── 1회차: 추첨 완료, 등수별 데모 ────────────────────────────
        draw1 = Draw.objects.create(
            round_no=1,
            n1=1, n2=2, n3=3, n4=4, n5=5, n6=6,
            bonus=7,
            status=Draw.Status.CLOSED,
            draw_date=timezone.now(),
        )

        demo = [
            (alice, [1, 2, 3, 4, 5, 6],  Ticket.PickType.MANUAL),  # 1등
            (bob,   [1, 2, 3, 4, 5, 7],  Ticket.PickType.MANUAL),  # 2등 (+보너스)
            (carol, [1, 2, 3, 4, 5, 8],  Ticket.PickType.MANUAL),  # 3등
            (alice, [1, 2, 3, 4, 8, 9],  Ticket.PickType.AUTO),    # 4등
            (bob,   [1, 2, 3, 8, 9, 10], Ticket.PickType.AUTO),    # 5등
            (carol, [8, 9, 10, 11, 12, 13], Ticket.PickType.AUTO), # 꽝
        ]

        for user, nums, pick_type in demo:
            ticket = Ticket(
                user=user, draw=draw1,
                n1=nums[0], n2=nums[1], n3=nums[2],
                n4=nums[3], n5=nums[4], n6=nums[5],
                pick_type=pick_type, price=1000,
            )
            ticket.save()
            rank, prize = evaluate_ticket(ticket, draw1)
            ticket.rank = rank
            ticket.prize = prize
            ticket.save(update_fields=["rank", "prize"])
            user.balance = user.balance - 1000 + prize
            user.save(update_fields=["balance"])

        # ── 2회차: 판매 중 (실 서비스 흐름) ──────────────────────────
        draw2 = Draw.objects.create(round_no=2)
        purchase_ticket(alice, draw2, [3, 7, 11, 22, 33, 44], Ticket.PickType.MANUAL)
        purchase_ticket(bob, draw2, generate_auto_numbers(), Ticket.PickType.AUTO)
        purchase_ticket(carol, draw2, generate_auto_numbers(), Ticket.PickType.AUTO)

        self.stdout.write(self.style.SUCCESS("시드 데이터 생성 완료."))
        self.stdout.write("  계정: admin/adminpass (staff), alice/alicepass, bob/bobpass, carol/carolpass")
        self.stdout.write(f"  1회차 추첨완료(당첨자 5명) / 2회차 판매중(3장 구매)")
