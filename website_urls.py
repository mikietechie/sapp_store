from django.urls import path
from sapp_store.views import website

urlpatterns = [
    path("", website.index_view),
    path("store/", website.store_view),
    path("cart/", website.cart_view),
    path("checkout/", website.checkout_view),
    path("product/<str:string>/<int:id>/", website.product_view),
]
