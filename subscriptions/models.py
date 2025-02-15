from django.db import models

# Create your models here.

MONTHLY = 'monthly'
YEARLY = 'yearly'

PLAN_TYPE_CHOICES = (
    (MONTHLY, 'Monthly'),
    (YEARLY, 'Yearly'),
)

class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(choices=PLAN_TYPE_CHOICES ,max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

class Subscription(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True)
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, db_index=True)
    coupon_code = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
