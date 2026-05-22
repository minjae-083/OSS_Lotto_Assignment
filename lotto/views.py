from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ManualTicketForm
from .models import Draw, Ticket
from .services import generate_auto_numbers, purchase_ticket


def home_view(request):
    open_draw = Draw.objects.filter(status=Draw.Status.OPEN).order_by("round_no").first()
    recent_closed = Draw.objects.filter(status=Draw.Status.CLOSED).order_by("-round_no")[:3]
    return render(request, "lotto/home.html", {
        "open_draw": open_draw,
        "recent_closed": recent_closed,
    })


@login_required
def buy_view(request):
    open_draw = Draw.objects.filter(status=Draw.Status.OPEN).order_by("round_no").first()
    if open_draw is None:
        messages.warning(request, "현재 판매 중인 회차가 없습니다.")
        return redirect("lotto:home")

    form = ManualTicketForm()

    if request.method == "POST":
        pick_type = request.POST.get("pick_type", Ticket.PickType.MANUAL)

        if pick_type == Ticket.PickType.AUTO:
            numbers = generate_auto_numbers()
            try:
                ticket = purchase_ticket(request.user, open_draw, numbers, pick_type)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
            else:
                messages.success(request, f"자동 구매 완료: {ticket.numbers()}")
            return redirect("lotto:buy")

        form = ManualTicketForm(request.POST)
        if form.is_valid():
            try:
                ticket = purchase_ticket(
                    request.user, open_draw, form.cleaned_data["numbers"], Ticket.PickType.MANUAL,
                )
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
            else:
                messages.success(request, f"수동 구매 완료: {ticket.numbers()}")
                return redirect("lotto:buy")

    return render(request, "lotto/buy.html", {
        "open_draw": open_draw,
        "form": form,
    })


@login_required
def my_tickets_view(request):
    tickets = request.user.tickets.select_related("draw").order_by("-purchased_at")
    return render(request, "lotto/my_tickets.html", {"tickets": tickets})


@login_required
def check_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    return render(request, "lotto/check.html", {"ticket": ticket})
