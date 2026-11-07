

import re
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.contrib import messages

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.db import transaction

from .models import Product, Order, OrderItem, Cart, CartItem


# ==========================================
# HOMEPAGE
# ==========================================

@ensure_csrf_cookie
def home(request):

    products = Product.objects.all().order_by('-created_at')

    search_query = request.GET.get('search', '')

    if search_query:
        products = products.filter(name__icontains=search_query)

    category = request.GET.get('category', '')

    if category:
        products = products.filter(category=category)

    context = {
        'products': products,
        'search_query': search_query,
        'selected_category': category,
        'total_products': products.count(),
    }

    return render(request, 'store/home.html', context)


# ==========================================
# PRODUCT DETAIL
# ==========================================

def product_detail(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    return render(request, 'store/product_detail.html', {
        'product': product
    })


# ==========================================
# CART DATA HELPER
# ==========================================

def get_cart_data(request):

    items = []
    total = Decimal('0.00')
    cart_count = 0

    # Logged-out visitors always see an empty cart.
    if not request.user.is_authenticated:
        return {
            'items': [],
            'total': 0,
            'cart_count': 0,
        }

    # Get or create the logged-in user's cart.
    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_items = CartItem.objects.filter(
        cart=cart
    ).select_related('product')

    for cart_item in cart_items:

        product = cart_item.product
        quantity = cart_item.quantity

        # Remove products that are no longer available.
        if product.stock <= 0:
            cart_item.delete()
            continue

        # Do not allow cart quantity to exceed available stock.
        if quantity > product.stock:
            quantity = product.stock
            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity'])

        price = product.price
        subtotal = price * quantity

        items.append({
            'id': product.id,
            'name': product.name,
            'price': float(price),
            'quantity': quantity,
            'stock': product.stock,
            'subtotal': round(float(subtotal), 2),
        })

        total += subtotal
        cart_count += quantity

    return {
        'items': items,
        'total': round(float(total), 2),
        'cart_count': cart_count,
    }


# ==========================================
# CART DETAIL
# ==========================================

def cart_detail(request):

    data = get_cart_data(request)

    return JsonResponse(data)


# ==========================================
# ADD PRODUCT TO CART
# ==========================================

@require_POST
def cart_add(request, product_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            'message': 'Please log in to add products to your cart.',
            'login_required': True,
        }, status=401)

    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        return JsonResponse({
            'message': 'This product is out of stock.'
        }, status=400)

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not item_created:

        if cart_item.quantity >= product.stock:
            return JsonResponse({
                'message': 'Maximum available stock reached.'
            }, status=400)

        cart_item.quantity += 1
        cart_item.save(update_fields=['quantity'])

    return JsonResponse(get_cart_data(request))


# ==========================================
# UPDATE PRODUCT QUANTITY
# ==========================================

@require_POST
def cart_update(request, product_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            'message': 'Please log in first.',
            'login_required': True,
        }, status=401)

    try:
        quantity = int(request.POST.get('quantity', 1))

    except (ValueError, TypeError):
        return JsonResponse({
            'message': 'Invalid quantity.'
        }, status=400)

    cart_item = get_object_or_404(
        CartItem,
        cart__user=request.user,
        product_id=product_id
    )

    product = cart_item.product

    if quantity <= 0:

        cart_item.delete()

    elif quantity > product.stock:

        return JsonResponse({
            'message': f'Only {product.stock} items are available.'
        }, status=400)

    else:

        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity'])

    return JsonResponse(get_cart_data(request))


# ==========================================
# REMOVE PRODUCT FROM CART
# ==========================================

@require_POST
def cart_remove(request, product_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            'message': 'Please log in first.',
            'login_required': True,
        }, status=401)

    CartItem.objects.filter(
        cart__user=request.user,
        product_id=product_id
    ).delete()

    return JsonResponse(get_cart_data(request))


# ==========================================
# USER REGISTRATION
# ==========================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(
                request,
                'Your account has been created successfully!'
            )

            return redirect('home')

    else:

        form = UserCreationForm()

    return render(request, 'store/register.html', {
        'form': form
    })


# ==========================================
# USER LOGIN
# ==========================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                'You have logged in successfully!'
            )

            return redirect('home')

    else:

        form = AuthenticationForm()

    return render(request, 'store/login.html', {
        'form': form
    })


# ==========================================
# USER LOGOUT
# ==========================================

@require_POST
def logout_view(request):

    # The database cart is preserved automatically.
    # Django logout clears the authentication session.
    logout(request)

    messages.success(
        request,
        'You have logged out successfully!'
    )

    return redirect('home')


# ==========================================
# CHECKOUT
# ==========================================

@login_required
def checkout(request):

    cart_data = get_cart_data(request)
    items = cart_data['items']

    if not items:

        messages.error(request, 'Your cart is empty.')
        return redirect('home')

    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        # Check required fields
        if not all([
            full_name,
            email,
            phone,
            address,
            city,
            postal_code
        ]):

            messages.error(request, 'Please fill in all fields.')
            return redirect('checkout')

        # Validate customer name
        if len(full_name) < 3:

            messages.error(request, 'Please enter a valid full name.')
            return redirect('checkout')

        # Validate email
        try:
            validate_email(email)

        except ValidationError:

            messages.error(
                request,
                'Please enter a valid email address.'
            )
            return redirect('checkout')

        # Validate Indian mobile number
        if not re.fullmatch(r'(?:\+91[- ]?)?[6-9]\d{9}', phone):

            messages.error(
                request,
                'Please enter a valid 10-digit Indian mobile number.'
            )
            return redirect('checkout')

        # Validate Indian PIN code
        if not re.fullmatch(r'[1-9]\d{5}', postal_code):

            messages.error(
                request,
                'Please enter a valid 6-digit PIN code.'
            )
            return redirect('checkout')

        # Place order
        try:

            with transaction.atomic():

                locked_products = {}

                # Lock and check stock again
                for item in items:

                    product = Product.objects.select_for_update().get(
                        id=item['id']
                    )

                    quantity = item['quantity']

                    if product.stock < quantity:

                        raise ValueError(
                            f'Only {product.stock} units of '
                            f'{product.name} are available.'
                        )

                    locked_products[item['id']] = product

                # Calculate total
                total = Decimal('0.00')

                for item in items:

                    product = locked_products[item['id']]

                    total += product.price * item['quantity']

                # Create order
                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    total_amount=total
                )

                # Create order items and reduce stock
                for item in items:

                    product = locked_products[item['id']]
                    quantity = item['quantity']

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        price=product.price,
                        quantity=quantity
                    )

                    product.stock -= quantity

                    product.save(update_fields=['stock'])

                # Clear only this user's database cart.
                CartItem.objects.filter(
                    cart__user=request.user
                ).delete()

            messages.success(
                request,
                f'Your order #{order.id} has been placed successfully!'
            )

            return redirect(
                'order_confirmation',
                order_id=order.id
            )

        except (Product.DoesNotExist, ValueError) as error:

            messages.error(request, str(error))
            return redirect('checkout')

    return render(request, 'store/checkout.html', {
        'items': items,
        'total': cart_data['total']
    })


# ==========================================
# MY ORDERS
# ==========================================

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related('items').order_by('-created_at')

    return render(request, 'store/my_orders.html', {
        'orders': orders
    })


# ==========================================
# ORDER CONFIRMATION
# ==========================================

@login_required
def order_confirmation(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        id=order_id,
        user=request.user
    )

    return render(request, 'store/order_confirmation.html', {
        'order': order
    })
