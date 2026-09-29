from django.urls import path
from . import views

urlpatterns = [
  path("products/", views.products, name="products"),
  path("orders/", views.orders, name="orders"),
  path("drinks/",views.get_drinks, name="drinks"),
  path("measurements",views.get_measurements, name="measurements"),
  path("all_products/", views.all_products, name="all products"),
  path("product/create", views.create, name="product create"),
  path("variant", views.get_variant, name="variant"),
  path("variant/update", views.update_variant, name="update variant"),
  path("image",views.upload_image, name="upload-image")
]
