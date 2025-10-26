from django.urls import path
from . import views

urlpatterns = [
    # Webpage URLs
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:jewelry_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout URLs
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_payment, name='process_payment'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('orders/history/', views.order_history, name='order_history'),

    # Authentication URLs
    path('accounts/signup/', views.signup, name='signup'),

    # Existing API URLs (if you added them previously)
    # path('api/jewelry/', ...),
]