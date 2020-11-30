from django.contrib import admin
from django.urls import path
from account.views import (
    RegisterView,
    home_view,
    logout_view,
    login_view,
    trial,
    hook,
    profile,
    cancel_subscription,
    remove,
    make_default,
    add_card,
    subscribe
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('logout/', logout_view, name='logout'),
    path('login/', login_view, name='login'),
    path('register/', RegisterView.as_view(), name='register'),            # Registration view using django-registration
    path('trial/', trial, name='trial'),                                   # Subscription view
    path('hook/', hook, name='hook'),
    path('profile/', profile, name='profile'),
    path('profile/cancel_sub/', cancel_subscription, name='cancel_sub'),
    path('profile/remove/', remove, name='remove'),                        # Removing a card
    path('profile/make_default/', make_default, name='make_default'),      # Making a card the default
    path('profile/add_card/', add_card, name='add_card'),
    path('trial/subscribe/', subscribe, name='subscribe'),                 # When confirming the subscription
]
