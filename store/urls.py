from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos, name='pos'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('change/<int:pk>/', views.change, name='change'),
]
