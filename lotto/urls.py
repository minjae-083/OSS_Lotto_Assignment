from django.urls import path

from . import views


app_name = "lotto"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("buy/", views.buy_view, name="buy"),
    path("my-tickets/", views.my_tickets_view, name="my_tickets"),
    path("check/<int:ticket_id>/", views.check_view, name="check"),
]
