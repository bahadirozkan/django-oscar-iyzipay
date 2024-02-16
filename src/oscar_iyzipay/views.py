import json
import locale
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.conf import settings
from django.shortcuts import get_object_or_404
from oscar.apps.checkout.views import ShippingAddressView as CoreShippingAddressView
from oscar.apps.checkout.views import ShippingMethodView as CoreShippingMethodView
from oscar.apps.checkout import views
from oscar.apps.payment import models
from oscar.core.loading import get_model, get_class
import phonenumbers
from ipware import get_client_ip
import iyzipay
import ujson

# get moodel
Order = get_model("order", "Order")
# get classes
OrderPlacementMixin = get_class("checkout.mixins", "OrderPlacementMixin")
RedirectRequired = get_class('payment.exceptions', 'RedirectRequired')
UnableToPlaceOrder = get_class('order.exceptions', 'UnableToPlaceOrder')
ShippingEventType = get_model("order", "ShippingEventType")
OrderNumberGenerator = get_class("order.utils", "OrderNumberGenerator")

iyipay_token = []

options = {
    'api_key': settings.IYZICO_API_KEY,
    'secret_key': settings.IYZICO_SECRET_KEY,
    'base_url': settings.IYZICO_BASE_URL
}


class ShippingAddressView(CoreShippingAddressView):
    success_url = reverse_lazy("checkout:preview")

class ShippingMethodView(CoreShippingMethodView):
    success_url = reverse_lazy("checkout:preview")

@method_decorator(csrf_exempt, name='dispatch')
class Iyzipay(OrderPlacementMixin, View):
    # get the info for iyzipay payment
    def get(self, request):
        submission = self.get_context_data()
        basket = submission['basket']
        paid_price = float(submission['order_total'].incl_tax)
        user = submission['user']
        usr_info = submission['shipping_address']
        last_login = user.last_login.strftime("%Y-%m-%d %H:%M:%S")
        register_time = user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
        phone_num = phonenumbers.format_number(usr_info.phone_number,
                                               phonenumbers.PhoneNumberFormat.E164)
        addrs = " ".join(f"""{usr_info.line1} {usr_info.line2}
                        {usr_info.line3} {usr_info.line4}""".split())
        # get ip from the client
        ipaddr, _ = get_client_ip(request)
        user_locale = locale.getlocale()[0]
        country = usr_info.country_id
        if ipaddr is None:
            # Unable to get the client's IP address
            # To be implemented
            pass

        buyer = {
            'id': str(10000 + basket.owner_id),
            'name': usr_info.first_name,
            'surname': usr_info.last_name,
            'gsmNumber': str(phone_num),
            'email': user.email,
            'identityNumber': str(usr_info.TCKN), # 11 digits
            'lastLoginDate': last_login, # '2015-10-05 12:43:35',
            'registrationDate':  register_time, # '2013-04-21 15:12:09',
            'registrationAddress': addrs,
            'ip':  ipaddr, # '85.34.78.112'
            'city': usr_info.line4,
            'country': country,
            'zipCode': usr_info.postcode
        }

        address = {
            'contactName': f"{usr_info.first_name} {usr_info.last_name}",
            'city': usr_info.line4,
            'country': country,
            'address': addrs,
            'zipCode': usr_info.postcode
        }

        basket_items = []
        line = basket.all_lines()
        price = 0
        for basket_item in line:
            # Items other than price is optional, change the id logic
            # and other items according to your needs
            line_price = float(basket_item.get_price_breakdown()[0][0])
            basket_items.append({
                'id': str(10000 + basket_item.id),
                'name': 'Name',
                'category1': 'Category 1',
                'category2': 'Category 2',
                'itemType': 'PHYSICAL',
                'price': line_price
                })
            price += line_price
        # Check if translation is active
        try:
            lang = submission['lang']
        except KeyError:
            lang = ""
        # Request dict to be sent to iyzipay
        req = {
            'locale': user_locale,
            # conversation id logic can be replaced
            'conversationId': str(100000000 + basket.id),
            'price': price,
            'paidPrice': paid_price,
            'currency': 'TRY',
            # baskedId logic can be replaced
            'basketId': str(100000 + basket.id),
            'paymentGroup': 'PRODUCT',
            # direct to correct language if i18N is TRUE
            'callbackUrl': f"/{lang}/checkout/post/" if lang else "/checkout/post/",
            'enabledInstallments': ['1'],
            'buyer': buyer,
            'shippingAddress': address,
            'billingAddress': address,
            'basketItems': basket_items,
        }

        checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(req, options)
        content = checkout_form_initialize.read().decode('utf-8')

        json_content = ujson.loads(content)
        iyipay_token.append(json_content["token"])
        return HttpResponse(json_content["checkoutFormContent"])

    def handle_order_placement(self):
        submission = self.get_context_data()
        # added to save the payment
        order_total = submission['order_total']
        order_number = OrderNumberGenerator().order_number(self.submission['basket'])
        source_type, __ = models.SourceType.objects.get_or_create(
            name="iyzico")
        source = models.Source(
            source_type=source_type,
            amount_allocated=order_total.incl_tax,
            reference=f'payment for order #{order_number}')
        self.add_payment_source(source)

        # Record payment event
        self.add_payment_event('Processed', order_total.incl_tax)

        # Place order
        super(Iyzipay, self).handle_order_placement(order_number, submission['user'],
                                                submission['basket'],
                                                submission['shipping_address'],
                                                submission['shipping_method'],
                                                submission['shipping_charge'],
                                                submission['billing_address'],
                                                order_total, surcharges=None)

    def handle_successful_order(self, order):
        """
        Handle the various steps required after an order has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Send confirmation message (normally an email)
        self.send_order_placed_email(order)
        # Flush all session data
        self.checkout_session.flush()
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id
        response = HttpResponseRedirect(self.get_success_url())
        # self.send_signal(self.request, response, order)
        return response

    # post data to validate payment
    def post(self, request):
        context = dict()

        request = {
            'locale': 'tr',
            'conversationId': '123456789',
            'token': iyipay_token[-1]
        }
        checkout_form_result = iyzipay.CheckoutForm().retrieve(request, options)
        result = checkout_form_result.read().decode('utf-8')
        sonuc = ujson.loads(result, object_pairs_hook=list)

        if sonuc[0][1] == 'success':
            context['success'] = 'Başarılı İŞLEMLER'
            try:
                self.handle_order_placement()
            except UnableToPlaceOrder as e:
                # It's possible that something will go wrong while trying to
                # actually place an order.  Not a good situation to be in as a
                # payment transaction may already have taken place, but needs
                # to be handled gracefully.
                msg = str(e)
                self.restore_frozen_basket()
                return HttpResponseRedirect(reverse('failure'), msg)
            except Exception as e:
                # Hopefully you only ever reach this in development
                self.restore_frozen_basket()
                return HttpResponseRedirect(reverse('failure'), e)

            return HttpResponseRedirect(reverse('success'), context)

        if sonuc[0][1] == 'failure':
            context['failure'] = 'Başarısız'
            return HttpResponseRedirect(reverse('failure'), context)

@method_decorator(csrf_exempt, name='dispatch')
class ThankYouView(views.ThankYouView):
    def dispatch(self, *args, **kwargs):
        return super(ThankYouView, self).dispatch(*args, **kwargs)

    def success(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('checkout:thank-you'))

def failure(request):
    error_msg = _("A problem occurred while placing this order. Please contact customer services.")
    template = 'oscar/checkout/failure.html'
    return render(request, template, {'failure': error_msg})
