from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("manage/", include("admin_panel.urls")),
    path("", include("lotto.urls")),
]
