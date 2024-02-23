"""
To add identification number and make the
phone number mandotory override the address
module of Django Oscar. See:
https://django-oscar.readthedocs.io/en/3.2.4/howto/how_to_customise_models.html

After doing above, add these to the models.py file of address module
"""

from django.db import models
from oscar.apps.address.abstract_models import AbstractShippingAddress
from oscar.apps.address.abstract_models import AbstractUserAddress
from django.core.validators import RegexValidator, MinLengthValidator
from phonenumber_field.modelfields import PhoneNumberField


class UserAddress(AbstractUserAddress):
    """Override AbstractUserAddress to add id no and make phone mandatory"""

    TCKN = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^\d{1,11}$"), MinLengthValidator(11)],
        default="11111111111",
    )

    def __str__(self):
        return f"{self.TCKN}"


class ShippingAddress(AbstractShippingAddress):
    """Override AbstractShippingAddress to add id no and make phone mandatory"""

    TCKN = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^\d{1,11}$"), MinLengthValidator(11)],
        default="11111111111",
    )

    def __str__(self):
        return f"{self.TCKN}"

    phone_number = PhoneNumberField(
        ("Phone number"),
        blank=False,
        help_text=("In case we need to call you about your order"),
    )


from oscar.apps.address.models import *

"""
DO THE SAME FOR order MODULE

After overriding the order module, add below
to models.py
"""

from address.models import (
    AbstractShippingAddress,
)

from oscar.apps.order.models import *  # noqa isort:skip

"""
IMPORTANT NOTICE: name the identification number as TCKN
This is what the django-oscar-iyzipay expects for processing
the payment.
"""
