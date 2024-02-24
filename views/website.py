from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.core.cache import cache

from sapp_store.models import Customer, Product, StoreSettings
from sapp_store.forms import FiltersForm

def inject_ctx(view_func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        # store_products = cache.get("store_products")
        # if not store_products:
        #     store_products = Product.objects.values("id", "name")
        #     cache.set("store_products", store_products)
        request: WSGIRequest = args[0]
        request.customer = Customer.objects.filter(user=request.user.pk).first()
        request.store_settings = StoreSettings.objects.first()
        # request.store_products = store_products
        return view_func(*args, **kwargs)
    return wrapper

@inject_ctx
def index_view(request: WSGIRequest):
    return render(request, "sapp_store/website/index.html")

@inject_ctx
def store_view(request: WSGIRequest):
    form = FiltersForm(request.GET)
    form.is_valid()
    products = list(Product.objects.filter(**form.get_cleaned_filters())) * 20
    page = Paginator(products, per_page=12, orphans=6).get_page(int(request.GET.get("page_number", 1)))
    return render(request, "sapp_store/website/store.html", {"page": page, "form": form})

@inject_ctx
def product_view(request: WSGIRequest, string: str, id: int):
    return render(request, "sapp_store/website/product.html", {"item": Product.objects.get(id=id)})

@inject_ctx
def cart_view(request: WSGIRequest):
    return render(request, "sapp_store/website/cart.html")

@inject_ctx
def checkout_view(request: WSGIRequest):
    return render(request, "sapp_store/website/checkout.html")
