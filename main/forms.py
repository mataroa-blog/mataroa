from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DjUserCreationForm
from django.core.mail import mail_admins


class UserCreationForm(DjUserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "blog_title"]


class InterestForm(forms.Form):
    email = forms.EmailField()

    def send_email(self):
        mail_admins("Interest form response", self.cleaned_data.get("email"))
