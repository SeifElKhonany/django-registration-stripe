from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django_registration.views import RegistrationView
from django.contrib.auth import login, authenticate, logout
from django_registration.signals import user_registered
from .forms import LoginForm
from .models import Subscription
from stripe.error import CardError
from mysite.settings import MEMBERSHIP_PRICE_ID
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core import serializers
from .forms import UpdateProfileForm
import stripe
import json


# Extend django-registration RegistrationView
class RegisterView(RegistrationView):
    # Url to navigate to after registration
    success_url = '/'
    template_name = 'account/register.html'

    def register(self, form):   # After form validation
        form.save()

        # Get user credentials to log in
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        login(self.request, user)

        # Send django-registration user_registered signal
        user_registered.send(sender=self.__class__)


def home_view(request):
    return render(request, 'account/home.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def login_view(request):
    context = dict()
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
        else:
            context['login_form'] = form
    else:
        context['login_form'] = LoginForm()

    return render(request, 'account/login.html', context)


@login_required             # This decorator requires being logged in to access the view
def profile(request):
    context = dict()
    cards = list()
    user = request.user
    if request.POST:
        form = UpdateProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Update credentials in Stripe
            stripe.Customer.modify(
                user.subscription.customer_id,
                name=form.cleaned_data['username'],
                email=form.cleaned_data['email']
            )
            # Redirect to avoid form resubmission on refresh
            redirect('profile')

        else:
            context['form'] = form

    # Get user's payment method ids
    payment_ids = user.subscription.payment_methods
    for payment_id in payment_ids:
        cards.append(stripe.PaymentMethod.retrieve(payment_id))

    context['cards'] = cards
    # Serialize the user to a json object so that the ajax request can send it back to a view
    context['user'] = serializers.serialize('json', [user, ])
    return render(request, 'account/profile.html', context)


# Called by an ajax post request to change the default card
@login_required
def make_default(request):
    card_id = request.POST['card_id']
    subscription = request.user.subscription
    stripe.Customer.modify(
        subscription.customer_id,
        invoice_settings={
            'default_payment_method': card_id,
        },
    )
    subscription.default_payment_method = card_id
    subscription.save()
    return HttpResponse(status=200)


# Called by an ajax post request to remove a card
@login_required
def remove(request):
    card_id = request.POST['card_id']
    subscription = request.user.subscription
    card = request.POST['card_no']
    # Remove the card from the customer's payment methods on Stripe
    stripe.PaymentMethod.detach(card_id)
    # Remove the card from the user's payment methods in the database
    subscription.payment_methods.remove(card_id)
    subscription.cards.remove(card)

    # If the user has more cards
    if subscription.payment_methods:
        # If the user is deleting the default card, make the default another one if they have one
        if card_id == subscription.default_payment_method:
            stripe.Customer.modify(
                subscription.customer_id,
                invoice_settings={
                    'default_payment_method': subscription.payment_methods[0],
                },
            )
            subscription.default_payment_method = subscription.payment_methods[0]

    # If the user has no cards, cancel their subscription
    else:
        # Cancel on Stripe
        stripe.Subscription.delete(subscription.subscription_id)
        subscription.subscription_id = ""
        # Change subscription state to Cancelled
        subscription.state = Subscription.CANCELLED

    subscription.save()

    return HttpResponse(status=200)


# Called by an ajax post request to add a card
@login_required
def add_card(request):
    error = ""
    user = request.user
    customer_id = user.subscription.customer_id

    # Convert the payment method object to add from JSON to dict
    payment_method = json.loads(request.POST['payment_method'])
    payment_method_id = payment_method['id']
    card = payment_method['card']['last4']

    s = user.subscription

    try:
        # Add the card if the user hadn't already added it before
        if card not in s.cards:

            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )

            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id,
                },
            )

            s.cards.append(card)
            s.payment_methods.append(payment_method_id)
            s.default_payment_method = payment_method_id
            s.save()

        else:
            error = 'You have already saved this payment method'

    # Errors like card_declined might arise
    except CardError as e:
        error = e.error.code

    return JsonResponse({"error": error})


@login_required
def cancel_subscription(request):
    subscription = request.user.subscription
    # Cancel on Stripe
    stripe.Subscription.delete(subscription.subscription_id)
    subscription.subscription_id = ""
    # Change subscription state to Cancelled
    subscription.state = Subscription.CANCELLED
    subscription.save()

    return redirect('profile')


# Called by an ajax post request to subscribe
@login_required
def subscribe(request):
    context = dict()
    s = request.user.subscription
    customer_id = s.customer_id
    # If the customer is using a new card
    if 'payment_method' in request.POST:
        # Convert the card object to use from JSON to dict
        payment_method = json.loads(request.POST['payment_method'])
        payment_method_id = payment_method['id']
        card = payment_method['card']['last4']

        try:
            # If the user hasn't already saved this card
            if card not in s.cards:
                # Attach the card to the customer on Stripe
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id,
                )

                # Make the card the default payment method of the customer
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id,
                    },
                )

                # Create a subscription on Stripe using the customer id and price id of the subscription
                subscription = stripe.Subscription.create(
                    customer=customer_id,
                    items=[
                        {
                            'price': MEMBERSHIP_PRICE_ID,
                        },
                    ],
                    trial_period_days=7,
                )

                s.subscription_id = subscription.id
                s.cards.append(card)
                s.payment_methods.append(payment_method_id)
                s.default_payment_method = payment_method_id
                s.state = Subscription.TRIALING
                s.save()

                try:
                    # Get the new subscription's setup intent's status to see if further action is required
                    setup_intent = stripe.Subscription.retrieve(
                        subscription['id'],
                        expand=['pending_setup_intent']
                    )['pending_setup_intent']

                    context['status'] = setup_intent['status']
                    context['client_secret'] = setup_intent['client_secret']

                # No further action required
                except TypeError:
                    context['status'] = None
                    context['client_secret'] = None

            else:
                context['error'] = 'You have already saved this payment method'

        # Errors like card_declined might arise
        except CardError as e:
            context['error'] = e.error.code

    # If the customer is using their default card
    else:
        # If the customer has a card
        if s.cards:
            try:
                subscription = stripe.Subscription.create(
                    customer=customer_id,
                    items=[
                        {
                            'price': MEMBERSHIP_PRICE_ID,
                        },
                    ],
                    trial_period_days=7,
                )

                s.subscription_id = subscription.id
                s.state = Subscription.TRIALING
                s.save()

                try:
                    setup_intent = stripe.Subscription.retrieve(
                        subscription['id'],
                        expand=['pending_setup_intent']
                    )['pending_setup_intent']

                    context['status'] = setup_intent['status']
                    context['client_secret'] = setup_intent['client_secret']

                except TypeError:
                    context['status'] = None
                    context['client_secret'] = None

            except CardError as e:
                context['error'] = e.error.code

        else:
            context['error'] = "You don't have any cards saved"

    return JsonResponse(context)


# Customer sign up
@login_required
def trial(request):
    s = request.user.subscription
    # User already subscribed
    if s.subscription_id:
        return redirect('profile')

    return render(request, 'account/trial.html', {"user": serializers.serialize('json', [request.user, ])})


# Webhook to receive events from Stripe and update subscription status accordingly
@csrf_exempt        # This decorator removes csrf token requirement to access the view
def hook(request):
    payload = request.body

    def update_subscription(customer_id, state):
        subscription = Subscription.objects.get(customer_id=customer_id)
        subscription.state = state
        subscription.save()

    # Retrieve event object
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )

    # Invalid payload
    except ValueError:
        return HttpResponse(status=400)

    if event.type == 'customer.subscription.deleted':   # canceled or unpaid
        if event.request == "":                         # deleted by stripe due to expiry
            update_subscription(event.data.object.customer, Subscription.UNPAID)

    elif event.type == 'invoice.payment_failed':        # past_due
        update_subscription(event.data.object.customer, Subscription.PAST_DUE)

    elif event.type == 'invoice.payment_succeeded':     # active
        update_subscription(event.data.object.customer, Subscription.ACTIVE)

    """ 
    In production mode, there would be events from customers created but Stripe doesn't send live events in test mode.
    Only the Stripe CLI can be used to manually test events
    """
    return HttpResponse(status=200)                     # Acknowledge event


