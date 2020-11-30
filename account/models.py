from django.db import models, migrations
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User


class Subscription(models.Model):

    # Constants to access choices easily
    INACTIVE = "INACTIVE"
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    PAST_DUE = "PAST_DUE"
    UNPAID = "UNPAID"

    STATE_CHOICES = [
        ("INACTIVE", "Inactive"),       # Hasn't started
        ("TRIALING", "Trialing"),
        ("ACTIVE", "Active"),           # Due invoices completed
        ("CANCELLED", "Cancelled"),     # Canceled by user
        ("PAST_DUE", "Past_due"),       # Last invoice failed
        ("UNPAID", "Unpaid"),           # 24 hours passed since last invoice failed
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default="INACTIVE")
    customer_id = models.CharField(max_length=100, default='')
    subscription_id = models.CharField(max_length=100, default='')

    # Stores the last 4 digits of a card to keep track (Stripe generates different card ids even it's the same card)
    cards = ArrayField(models.CharField(max_length=4), default=list)

    # Stores payment method ids
    payment_methods = ArrayField(models.CharField(max_length=100), default=list)
    default_payment_method = models.CharField(max_length=100, default='')

    # What is printed when printing the object
    def __str__(self):
        return self.user.username + "'s subscription: " + self.state
