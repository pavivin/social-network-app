from functools import lru_cache

from django.db import models
from passlib.context import CryptContext
from uuid_extensions import uuid7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


class City(models.TextChoices):
    YAROSLAVL = "Ярославль"
    ROSTOV = "Ростов"
    TUTAEV = "Тутаев"

    @classmethod
    @lru_cache
    def all(cls):
        return [e.value for e in cls]


class User(models.Model):
    class Role(models.TextChoices):
        CITIZEN = "citizen"
        GOVERNMENT = "government"

    id = models.UUIDField(primary_key=True, default=uuid7)
    first_name = models.CharField(max_length=50, null=True, default="Анонимный", blank=True)
    last_name = models.CharField(max_length=50, null=True, default="Пользователь", blank=True)
    email = models.CharField(max_length=254, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CITIZEN)
    image_url = models.ImageField(
        max_length=2000,
        null=True,
        default="https://voices-city.ru/api/storage/064e74c0198f7159800002e35c77df4a.jpg",
        blank=True,
    )
    hashed_password = models.CharField(max_length=128, default=get_password_hash("string"))

    city = models.CharField(max_length=9, choices=City.choices, default=None, blank=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    birthdate = models.DateField(null=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "users"
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"


class Initiative(models.Model):
    class CitizenCategory(models.TextChoices):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"
        SURVEY = "SURVEY"
        PROJECT = "PROJECT"
        BUILDING = "BUILDING"

    class Category(models.TextChoices):
        PROBLEM = "PROBLEM"
        EVENT = "EVENT"
        DECIDE_TOGETHER = "DECIDE_TOGETHER"
        SURVEY = "SURVEY"
        PROJECT = "PROJECT"
        BUILDING = "BUILDING"

    class Status(models.TextChoices):
        ACTIVE = "active"
        SOLVED = "solved"

    class TagsCategory(models.TextChoices):
        PROBLEM = "Новость"
        EVENT = "Событие"
        DECIDE_TOGETHER = "Решаем вместе"
        SURVEY = "Опрос"
        PROJECT = "Проект"
        BUILDING = "Строительство"

    id = models.UUIDField(primary_key=True, default=uuid7)
    city = models.CharField(max_length=35, choices=City.choices)
    main_text = models.TextField()
    title = models.TextField()
    images = models.JSONField(null=True, blank=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    reposts_count = models.IntegerField(default=0)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.ACTIVE)
    to_date = models.DateField(null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    ar_model = models.CharField(max_length=2000, null=True, blank=True)
    event_direction = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    created_at = models.DateTimeField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = "initiatives"
        verbose_name = "инициатива"
        verbose_name_plural = "инициативы"
