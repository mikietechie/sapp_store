from django.urls import path

from sapp_store.views.space import index_view

urlpatterns = [
    path('', index_view),
]