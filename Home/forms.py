from .models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm

class CustomUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']


class SpellCheckForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='Enter text')