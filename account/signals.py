from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Subscription
import stripe


# Receive a signal that a new user is registered and create a customer instance for them on Stripe
@receiver(post_save, sender=User)
def subscribe(sender, instance, created, **kwargs):
    if created:
        customer = stripe.Customer.create(name=instance.username, email=instance.email)
        s = Subscription.objects.create(user=instance, customer_id=customer.id)
        s.save()





