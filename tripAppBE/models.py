from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    trip_id = models.AutoField(primary_key=True)
    trip_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserTrip(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('trip', 'user')


class Cost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    cost_id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    cost_name = models.CharField(max_length=255)
    overall_value = models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.BooleanField(default=False)


class Splited(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="splits")
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payed_splits")
    cost = models.ForeignKey(Cost, on_delete=models.CASCADE)
    payment = models.BooleanField(default=False)
    split_value = models.DecimalField(max_digits=10, decimal_places=2)
    to_pay_back_value = models.DecimalField(max_digits=10, decimal_places=2)
    pay_back_value = models.DecimalField(max_digits=10, decimal_places=2)