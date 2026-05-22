from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render

from lotto.models import Draw, Ticket
from lotto.services import create_next_draw, run_draw


@staff_member_required
def sales_view(request):
    draws = (
        Draw.objects
        .annotate(
            ticket_count=Count("tickets"),
            revenue=Sum("tickets__price"),
            manual_count=Count("tickets", filter=Q(tickets__pick_type=Ticket.PickType.MANUAL)),
            auto_count=Count("tickets", filter=Q(tickets__pick_type=Ticket.PickType.AUTO)),
        )
        .order_by("-round_no")
    )
    return render(request, "admin_panel/sales.html", {"draws": draws})


@staff_member_required
def draw_view(request):
    open_draw = Draw.objects.filter(status=Draw.Status.OPEN).order_by("round_no").first()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            if open_draw is not None:
                messages.warning(request, "이미 판매 중인 회차가 있습니다.")
            else:
                new = create_next_draw()
                messages.success(request, f"{new.round_no}회차를 열었습니다.")
        elif action == "run":
            try:
                drawn, winners = run_draw(open_draw.round_no)
            except (ValidationError, AttributeError) as exc:
                messages.error(request, f"추첨 실패: {exc}")
            else:
                summary = ", ".join(f"{r}등 {c}명" for r, c in winners.items() if c)
                messages.success(
                    request,
                    f"{drawn.round_no}회차 추첨 완료 — 번호 {drawn.winning_numbers()} + 보너스 {drawn.bonus}. "
                    f"{summary or '당첨자 없음'}",
                )
        return redirect("admin_panel:draw")

    recent_closed = Draw.objects.filter(status=Draw.Status.CLOSED).order_by("-round_no")[:5]
    return render(request, "admin_panel/draw.html", {
        "open_draw": open_draw,
        "recent_closed": recent_closed,
    })


@staff_member_required
def winners_view(request):
    draws = (
        Draw.objects.filter(status=Draw.Status.CLOSED)
        .annotate(
            r1=Count("tickets", filter=Q(tickets__rank=1)),
            r2=Count("tickets", filter=Q(tickets__rank=2)),
            r3=Count("tickets", filter=Q(tickets__rank=3)),
            r4=Count("tickets", filter=Q(tickets__rank=4)),
            r5=Count("tickets", filter=Q(tickets__rank=5)),
            total_payout=Sum("tickets__prize"),
        )
        .order_by("-round_no")
    )
    winning_tickets = (
        Ticket.objects.filter(rank__gt=0)
        .select_related("user", "draw")
        .order_by("-draw__round_no", "rank")[:50]
    )
    return render(request, "admin_panel/winners.html", {
        "draws": draws,
        "winning_tickets": winning_tickets,
    })
