from django.urls import path
from . import views

urlpatterns = [
    path('checkout/get/', views.Iyzipay.as_view(), name='get'),
    path('checkout/post/', views.Iyzipay.as_view(), name='post'),
    path('checkout/success/', views.success, name='success'),
    path('checkout/failure/', views.failure, name='failure'),
]
