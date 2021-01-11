from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DjUserCreationForm
from django.core import validators as dj_validators

from main import models


class UserCreationForm(DjUserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username"]


class NotificationForm(forms.ModelForm):
    class Meta:
        model = models.Notification
        fields = ["email"]


class UploadTextFilesForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))


class UploadImagesForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        validators=[
            dj_validators.FileExtensionValidator(
                ["jpeg", "jpg", "png", "svg", "gif", "webp", "tiff", "tif", "bmp"]
            )
        ],
    )
