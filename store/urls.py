
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Shopping cart
    path('cart/', views.cart_detail, name='cart_detail'),

    path(
        'cart/add/<int:product_id>/',
        views.cart_add,
        name='cart_add'
    ),

    path(
        'cart/update/<int:product_id>/',
        views.cart_update,
        name='cart_update'
    ),

    path(
        'cart/remove/<int:product_id>/',
        views.cart_remove,
        name='cart_remove'
    ),
     # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Orders
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path(
        'order-confirmation/<int:order_id>/',
        views.order_confirmation,
        name='order_confirmation'
    ),
    path(
    'product/<int:product_id>/',
    views.product_detail,
    name='product_detail'
),
]
