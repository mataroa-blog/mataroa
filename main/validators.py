from django.core import validators as dj_validators
from django.core.exceptions import ValidationError


class AlphanumericHyphenValidator(dj_validators.RegexValidator):
    regex = r"^[a-z\d-]+\Z"
    message = "Invalid value. Should include only lowercase letters, numbers, and -"
    flags = 0


class HyphenOnlyValidator(dj_validators.RegexValidator):
    regex = r"^[-]*$"
    message = "Invalid value. Cannot be just hyphens."
    inverse_match = True
    flags = 0


def validate_domain_name(value):
    if "." not in value:
        raise ValidationError("Invalid domain name")
