from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/products/update/$', consumers.ProductUpdateConsumer.as_asgi()),
]
