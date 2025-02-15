from django.db import models

# Create your models here.

class Coupon(models.Model):
    discount_code = models.CharField(max_length=255, unique=True)
    discount_percentage = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    max_discount = models.FloatField(blank=True, null=True)
    usage_limit = models.PositiveIntegerField()
