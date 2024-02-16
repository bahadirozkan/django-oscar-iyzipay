from django.db import models
from oscar.apps.address.abstract_models import AbstractShippingAddress
from oscar.apps.address.abstract_models import AbstractUserAddress
from django.core.validators import RegexValidator, MinLengthValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext as _

class UserAddress(AbstractUserAddress):
    TCKN = models.CharField(max_length=11, validators=[RegexValidator(r'^\d{1,11}$'), MinLengthValidator(11)], default="")

    def __str__(self):
        return f"{self.TCKN}"

class ShippingAddress(AbstractShippingAddress):
    TCKN = models.CharField(max_length=11, validators=[RegexValidator(r'^\d{1,11}$'), MinLengthValidator(11)], default="")

    def __str__(self):
        return f"{self.TCKN}"
    
    phone_number = PhoneNumberField(
        ("Phone number"),
        blank=False,
        help_text=_("In case we need to call you about your order"),
    )

from oscar.apps.address.models import *  # noqa isort:skip
