from django.conf import settings
from django.db import models


TICKET_PRICE = 1000


class Draw(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "판매중"
        CLOSED = "CLOSED", "추첨완료"

    round_no = models.PositiveIntegerField(unique=True)
    draw_date = models.DateTimeField(null=True, blank=True)
    n1 = models.PositiveSmallIntegerField(null=True, blank=True)
    n2 = models.PositiveSmallIntegerField(null=True, blank=True)
    n3 = models.PositiveSmallIntegerField(null=True, blank=True)
    n4 = models.PositiveSmallIntegerField(null=True, blank=True)
    n5 = models.PositiveSmallIntegerField(null=True, blank=True)
    n6 = models.PositiveSmallIntegerField(null=True, blank=True)
    bonus = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-round_no"]

    def __str__(self):
        return f"{self.round_no}회차 ({self.get_status_display()})"

    def winning_numbers(self):
        return [self.n1, self.n2, self.n3, self.n4, self.n5, self.n6]


class Ticket(models.Model):
    class PickType(models.TextChoices):
        MANUAL = "MANUAL", "수동"
        AUTO = "AUTO", "자동"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    draw = models.ForeignKey(
        Draw,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    n1 = models.PositiveSmallIntegerField()
    n2 = models.PositiveSmallIntegerField()
    n3 = models.PositiveSmallIntegerField()
    n4 = models.PositiveSmallIntegerField()
    n5 = models.PositiveSmallIntegerField()
    n6 = models.PositiveSmallIntegerField()
    pick_type = models.CharField(max_length=6, choices=PickType.choices)
    purchased_at = models.DateTimeField(auto_now_add=True)
    # null=미추첨, 0=꽝, 1~5=등수
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    prize = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=TICKET_PRICE)

    class Meta:
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.draw.round_no}회차 - {self.user.username}"

    def numbers(self):
        return [self.n1, self.n2, self.n3, self.n4, self.n5, self.n6]

    def save(self, *args, **kwargs):
        nums = sorted([self.n1, self.n2, self.n3, self.n4, self.n5, self.n6])
        self.n1, self.n2, self.n3, self.n4, self.n5, self.n6 = nums
        super().save(*args, **kwargs)
