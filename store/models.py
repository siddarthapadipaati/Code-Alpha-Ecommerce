
from django.db import models
from django.conf import settings


# ==========================================
# PRODUCT MODEL
# ==========================================

class Product(models.Model):

    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('accessories', 'Accessories'),
    ]

    name = models.CharField(max_length=200)

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    stock = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================================
# USER CART MODEL
# ==========================================

class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.username}"


# ==========================================
# CART ITEM MODEL
# ==========================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_product_per_cart'
            )
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# ==========================================
# ORDER MODEL
# ==========================================

class Order(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# ==========================================
# ORDER ITEM MODEL
# ==========================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    product_name = models.CharField(max_length=200)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.product_name
