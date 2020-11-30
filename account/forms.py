from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django_registration.forms import RegistrationForm


class LoginForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean(self):  # gets executed before the form can do anything
        if self.is_valid():
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']
            if not authenticate(username=username, password=password):
                raise forms.ValidationError("Invalid login")


class UpdateProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'email']



