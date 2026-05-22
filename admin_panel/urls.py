from django.urls import path

from . import views


app_name = "admin_panel"

urlpatterns = [
    path("sales/", views.sales_view, name="sales"),
    path("draw/", views.draw_view, name="draw"),
    path("winners/", views.winners_view, name="winners"),
]
