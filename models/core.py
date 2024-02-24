from decimal import Decimal as D
import typing

from django.db import models
from django.utils.functional import cached_property
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.request import Request
from django import forms
from django.core.handlers.wsgi import WSGIRequest

from sapp.models import SM, ImageField, AbstractUser, AbstractSettings, AbstractType


class Customer(SM):
    icon = "fas fa-user-tag"
    list_field_names = ("id", "user")
    queryset_names = ("carts",)
    api_methods = ("get_active_cart_api", "get_customer_ctx_api")

    user: models.ForeignKey[AbstractUser] = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="user_sapp_furniture_store_customer",
    )

    @cached_property
    def carts(self):
        return Cart.objects.filter(customer=self.user)

    @property
    def active_cart(self):
        return Cart.objects.get_or_create(customer_id=self.pk, checked_out=False)[0]

    @classmethod
    def get_active_cart_api(cls, request: Request, kwds: dict):
        customer = Customer.objects.get(user_id= request.user.id)
        serializer_class = Cart.get_serializer(request, Cart.serializer_cart_fields)
        return serializer_class(instance=customer.active_cart).data

    @classmethod
    def get_customer_ctx_api(cls, request: Request, kwds: dict):
        customer = Customer.objects.get(user_id= request.user.id)
        serializer_class = Customer.get_serializer(request, ("id", "user"))
        return serializer_class(instance=customer).data

    def __str__(self):
        return f"{self.str_id} - {self.user.get_full_name()}"

    def after_save(self, is_creation: bool):
        self.active_cart
        return super().after_save(is_creation)


# class Brand(AbstractType):
#     pass


class Material(AbstractType):
    pass


class Category(SM):
    class Meta(SM.Meta):
        verbose_name_plural = "Categories"

    icon = "fas fa-tag"
    list_field_names = ("id", "name", "image")
    api_methods = ("get_category_product_stats_api",)

    name = models.CharField(max_length=256)
    image = ImageField()
    description = models.TextField()

    def __str__(self):
        return self.name

    @cached_property
    def products(self):
        return Product.objects.filter(category=self)

    @classmethod
    def get_category_product_stats_api(cls, request: Request, kwds: dict):
        return cls.get_category_product_stats()

    @classmethod
    def get_category_product_stats(cls):
        data = {}
        for i in Category.objects.all():
            data[f"{i.name}"] = i.products.count()
        return data


class Specification(SM):
    icon = "fas fa-tasks"
    list_field_names = ("id", "text")

    text = models.TextField(max_length=512)
    group = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.text[:100]


class Product(SM):
    icon = "fab fa-product-hunt"
    list_field_names = ("id", "name", "image", "category", "price", "stock_qty")
    filter_field_names = ("category", )

    name = models.CharField(max_length=256)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # brand = models.ForeignKey(Brand, on_delete=models.PROTECT, blank=True, null=True)
    image = ImageField()
    design_image = ImageField(blank=True, null=True)
    image_1 = ImageField(blank=True, null=True)
    image_2 = ImageField(blank=True, null=True)
    image_3 = ImageField(blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=32, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    made_in = models.CharField(max_length=256, blank=True, null=True)
    specifications = models.ManyToManyField(Specification, blank=True)
    similar = models.ManyToManyField("self", blank=True)

    material = models.ForeignKey(Material, on_delete=models.PROTECT, blank=True, null=True)
    length = models.CharField(max_length=32, blank=True, null=True)
    width = models.CharField(max_length=32, blank=True, null=True)
    manufacturing_standard = models.CharField(max_length=128, blank=True, null=True)
    product_type = models.CharField(max_length=32, blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"{self.str_id} - {self.name}"

    @classmethod
    def get_filters_form(cls, request: WSGIRequest, _fields: typing.Iterable = None):
        super_form = super().get_filters_form(request, _fields)
        class FormClass(super_form):
            name__icontains = forms.CharField(label="Name Search", )
            description__icontains = forms.CharField(label="Desc Search", )
            price__gte = forms.DecimalField(decimal_places=2, label="Min Price")
            price__lte = forms.DecimalField(decimal_places=2, label="Max Price")
        return FormClass


class Cart(SM):
    icon = "fas fa-shopping-cart"
    list_field_names = ("id", "customer", "checked_out", "creation_timestamp")
    filter_field_names = ("customer", "checked_out")
    queryset_names = ("cart_items",)
    api_methods = ("update_cart_items_api",)
    serializer_cart_fields = ("id", "checked_out", "total", "items_count", "serialized_cart_items")
    cart_item_list_field_names = ("id", "product", "unit_price", "qty", "line_total")
    # confirm_delete = True

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    checked_out = models.BooleanField(default=False)
    items_count = models.PositiveSmallIntegerField(default=0)
    total = models.DecimalField(max_digits=32, decimal_places=2, default=D("0.00"))

    def __str__(self):
        return f"{self.str_id} - {self.customer}"

    @cached_property
    def cart_items(self):
        return CartItem.objects.filter(cart=self)

    @cached_property
    def cart_items_total(self):
        return self.cart_items.aggregate(sm=models.Sum("line_total"))["sm"] or D("0.00")

    @cached_property
    def cart_items_count(self):
        return self.cart_items.count()
    
    @SM.get_serialized_property(*cart_item_list_field_names, "serialized_product")
    def serialized_cart_items(self):
        return self.cart_items

    def sync_total_and_count(self):
        Cart.objects.filter(id=self.pk).update(
            total=self.cart_items_total, items_count=self.cart_items_count
        )

    def after_save(self, is_creation: bool):
        super_after_save = super().after_save(is_creation)
        self.sync_total_and_count()
        return super_after_save

    @classmethod
    def update_cart_items_api(cls, request: Request, kwds: dict):
        cart = cls.objects.get(id=request.data["cart_id"])
        product = Product.objects.get(id=request.data["product_id"])
        cart_item = cart.update_cart_items(product, request.data["qty"])
        if cart_item:
            serializer_class = CartItem.get_serializer(request, CartItem.list_field_names)
            return serializer_class(instance=cart_item).data

    def update_cart_items(self, product: Product, qty: int, action: str|None = None):
        item_in_cart = self.cart_items.filter(product=product).first()
        if item_in_cart:
            if qty:
                item_in_cart.qty = qty
                item_in_cart.save()
                return item_in_cart
            else:
                item_in_cart.delete()
        else:
            return CartItem.objects.create(cart=self, product=product, qty=qty)


class CartItem(SM):
    icon = "fas fa-box"
    list_field_names = Cart.cart_item_list_field_names
    filter_field_names = ("cart", "product")

    cart = models.ForeignKey(Cart, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=32, decimal_places=2, blank=True)
    line_total = models.DecimalField(max_digits=32, decimal_places=2, blank=True)

    def __str__(self):
        return f"{self.str_id} - {self.product}"

    def set_unit_price(self):
        self.unit_price = self.unit_price or self.product.price

    def set_line_total(self):
        self.line_total = self.unit_price * self.qty

    def save(self, *args, **kwargs):
        self.set_unit_price()
        self.set_line_total()
        return super().save(*args, **kwargs)

    def validate_cart_checked_out(self):
        if self.cart.checked_out:
            raise ValidationError(
                f"Cart has already been checkout out, you can't edit items anymore!"
            )

    def after_save(self, is_creation: bool):
        super_after_save = super().after_save(is_creation)
        self.cart.sync_total_and_count()
        return super_after_save
    
    @SM.get_serialized_property(*Product.list_field_names)
    def serialized_product(self):
        return self.product


class StoreSettings(AbstractSettings):
    featured_products = models.ManyToManyField(Product, blank=True)

    @cached_property
    def categories(self):
        return Category.objects.all()
