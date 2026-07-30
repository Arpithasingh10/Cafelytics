from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    roll_no = forms.CharField(max_length=30)
    class Meta:
        model = User
        fields = ("username","roll_no","first_name","last_name","email","password1","password2")
