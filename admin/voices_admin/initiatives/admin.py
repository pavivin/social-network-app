import re

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from .models import Initiative, User

a = re.compile(r"[\'\[\]\"]+")

UPLOAD_URL = "http://89.108.65.101:8000/" if settings.DEBUG else "localhost:8000"
DEFAULT_URL = "http://89.108.65.101:5000/"


@admin.register(User)
class UserAdminView(admin.ModelAdmin):
    list_display = ("image_tag", "first_name", "last_name", "city")
    fields = ("first_name", "last_name", "city", "role", "image_url", "district", "email")

    def save_model(self, request, obj: User, form, change):
        super().save_model(request, obj, form, change)
        if not obj.image_url.url.startswith(UPLOAD_URL) and not obj.image_url.url.startswith(DEFAULT_URL):
            obj.image_url = UPLOAD_URL + obj.image_url.url.removeprefix("/")

        obj.save()

    def image_tag(self, obj: User):
        return format_html(f'<img src="{obj.image_url}" style="max-width:200px; max-height:200px"/>')


@admin.register(Initiative)
class InitiativeAdminView(admin.ModelAdmin):
    list_display = ("image_tag", "title", "created_at", "user")
    fields = (
        "title",
        "city",
        "main_text",
        "images",
        "status",
        "from_date",
        "to_date",
        "ar_model",
        "event_direction",
        "user",
    )

    def image_tag(self, obj: Initiative):
        url = re.sub(a, "", str(obj.images))
        return format_html(f'<img src="{url}" style="max-width:200px; max-height:200px"/>')
