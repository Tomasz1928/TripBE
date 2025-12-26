from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class Trip(models.Model):
    trip_code = models.CharField(max_length=8, unique=True, db_index=True)
    trip_id = models.AutoField(primary_key=True)
    trip_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_trips")
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    default_currency = models.TextField(max_length=5)


class Cost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    cost_id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    cost_name = models.CharField(max_length=30)
    overall_value = models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.BooleanField(default=False)
    description = models.TextField(max_length=250)
    payed_currency = models.TextField(max_length=5)
    overall_value_main_currency = models.DecimalField(max_digits=10, decimal_places=2)


class TripParticipant(models.Model):
    Join_code = models.CharField(max_length=8, db_index=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nickname = models.CharField(max_length=25)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["Join_code"],
                condition=Q(user__isnull=True),
                name="unique_join_code_when_user_null"
            )
        ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trip", "user"],
                condition=Q(user__isnull=False),
                name="unique_user_per_trip"
            )
        ]

    def is_placeholder(self):
        return self.user is None

class Splited(models.Model):
    participant = models.ForeignKey(TripParticipant,  on_delete=models.CASCADE,  related_name="splits")
    payer = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name="payed_splits")
    cost = models.ForeignKey(Cost, on_delete=models.CASCADE)
    payment = models.BooleanField(default=False)
    split_value = models.DecimalField(max_digits=10, decimal_places=2)
    to_pay_back_value = models.DecimalField(max_digits=10, decimal_places=2)
    pay_back_value = models.DecimalField(max_digits=10, decimal_places=2)

    split_value_main_current = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    to_pay_back_value_main_current = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    pay_back_value_main_current = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)


