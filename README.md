# Django Oscar Iyzipay Integration

Integration between Django Oscar and Iyzipay for seamless payment processing.

[![Static Badge](https://img.shields.io/badge/pypi-v1.0.4-blue)](https://pypi.org/project/django-oscar-iyzipay/)

## Overview

This package provides integration between [Django Oscar](https://github.com/django-oscar/django-oscar) and [Iyzipay](https://github.com/iyzico/iyzipay-python) payment gateway, allowing Django Oscar-based e-commerce websites to process payments securely and efficiently using iyzico's payment services.

## Features

- Seamless integration between Django Oscar and Iyzipay payment gateway.
- Support for processing payments securely using Iyzipay's services.
- Easy installation and setup process.

## Installation

You can install `django-oscar-iyzipay` via pip:

```bash
pip install django-oscar-iyzipay
```

## Usage

To integrate Django Oscar with Iyzipay, follow these steps:

1.  Install the package using pip.
2.  Configure your Django project to use Iyzipay as the payment gateway.
	- Add oscar_iyzipay to INSTALLED_APPS
	```python
	'oscar_iyzipay',
	```
	- Add your iyzipay credentials inside settings.py
	```python
	IYZICO_API_KEY  =  <your iyzipay api key>
	IYZICO_SECRET_KEY  =  <your iyzipay secret key>
	IYZICO_BASE_URL  =  <iyzipay base url>
	```
	- Add oscar_iyzipay.urls to your url.py
	```python
	path('', include('oscar_iyzipay.oscar_iyzipay.urls')),
	```
	- iyzipay expects an identification number (11 digits) and a phone number (not mandatory in Oscar). How to do this can be found in the [add_model_items.py](https://github.com/bahadirozkan/django-oscar-iyzipay/tree/main/documentation/add_model_items.py).
3.	Finally override any Oscar template to direct to iyzipay gateway. An example is procided in [modify_template.html](https://github.com/bahadirozkan/django-oscar-iyzipay/tree/main/documentation/modify_template.html)


## Contributing

Contributions are welcome! Below are the main action points:

- [ ] Add sandbox
- [ ] Test for django-oscar 3.2
- [ ] Add tests
- [ ] Feature: Add enable installments option. (Default to 1)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/bahadirozkan/django-oscar-iyzipay/blob/main/LICENSE) file for details.

## Credits

This package is maintained by [Bahadır Özkan](https://github.com/bahadirozkan)

## Support

For support, bug reports, or feature requests, please open an issue on [GitHub](https://github.com/bahadirozkan/django-oscar-iyzipay/issues).

----------

**Disclaimer**: This package is not maintained officially by Django Oscar or Iyzipay. It is maintained by individual contributors. Use at your own discretion.
