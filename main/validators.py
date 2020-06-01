from django.core import validators
from django.utils.deconstruct import deconstructible


@deconstructible
class StrictUsernameValidator(validators.RegexValidator):
    regex = r"^[a-z\d-]+\Z"
    message = "Enter a valid username, it should include only lowercase letters, numbers, and -"
    flags = 0
