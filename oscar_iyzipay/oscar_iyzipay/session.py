from oscar.apps.checkout.session import CheckoutSessionMixin as CoreCheckoutSessionMixin
from oscar.apps.checkout import exceptions
from oscar.core.loading import get_class
from django.contrib import messages
from django import http
from . import tax

CheckoutSessionData = get_class("checkout.utils", "CheckoutSessionData")
SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")


class CheckoutSessionMixin(CoreCheckoutSessionMixin):
    """Overrides Oscar's CoreCheckoutSessionMixin to apply tax"""

    def dispatch(self, request, *args, **kwargs):
        """
        Assign the checkout session manager so it's available
        in all checkout views.
        """
        self.checkout_session = CheckoutSessionData(request)

        # Check if this view should be skipped
        try:
            self.check_skip_conditions(request)
        except exceptions.PassedSkipCondition as e:
            return http.HttpResponseRedirect(e.url)

        # Enforce any pre-conditions for the view.
        try:
            self.check_pre_conditions(request)
        except exceptions.FailedPreCondition as e:
            for message in e.messages:
                messages.warning(request, message)
            return http.HttpResponseRedirect(e.url)

        return super().dispatch(request, *args, **kwargs)

    def build_submission(self, **kwargs):
        """
        Return a dict of data that contains everything required for an order
        submission.  This includes payment details (if any).

        This can be the right place to perform tax lookups and apply them to
        the basket.
        """
        # Pop the basket if there is one, because we pass it as a positional
        # argument to methods below
        basket = kwargs.pop("basket", self.request.basket)
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(basket, shipping_address)
        billing_address = self.get_billing_address(shipping_address)
        submission = {
            "user": self.request.user,
            "basket": basket,
            "shipping_address": shipping_address,
            "shipping_method": shipping_method,
            "billing_address": billing_address,
            "order_kwargs": {},
            "payment_kwargs": {},
        }

        if not shipping_method:
            total = shipping_charge = surcharges = None
        else:
            shipping_charge = shipping_method.calculate(basket)
            surcharges = SurchargeApplicator(
                self.request, submission
            ).get_applicable_surcharges(
                self.request.basket, shipping_charge=shipping_charge
            )
            total = self.get_order_totals(
                basket, shipping_charge=shipping_charge, surcharges=surcharges, **kwargs
            )

        submission["shipping_charge"] = shipping_charge
        submission["order_total"] = total
        submission["surcharges"] = surcharges

        # If there is a billing address, add it to the payment kwargs as calls
        # to payment gateways generally require the billing address. Note, that
        # it normally makes sense to pass the form instance that captures the
        # billing address information. That way, if payment fails, you can
        # render bound forms in the template to make re-submission easier.
        if billing_address:
            submission["payment_kwargs"]["billing_address"] = billing_address

        # Allow overrides to be passed in
        submission.update(kwargs)

        # Set guest email after overrides as we need to update the order_kwargs
        # entry.
        user = submission["user"]
        if (
            not user.is_authenticated
            and "guest_email" not in submission["order_kwargs"]
        ):
            email = self.checkout_session.get_guest_email()
            submission["order_kwargs"]["guest_email"] = email

        # apply the tax here
        tax.apply_to(submission)
        return submission
