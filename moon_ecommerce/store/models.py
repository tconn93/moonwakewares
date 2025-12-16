from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Personal Information
    full_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Shipping Address
    shipping_street = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_zip = models.CharField(max_length=20, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, default='USA', blank=True, null=True)

    # Billing Address
    billing_street = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_zip = models.CharField(max_length=20, blank=True, null=True)
    billing_country = models.CharField(max_length=100, default='USA', blank=True, null=True)

    # Preferences
    same_billing_shipping = models.BooleanField(default=True, help_text="Use shipping address for billing")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

    def get_full_shipping_address(self):
        """Return formatted shipping address"""
        if not all([self.shipping_street, self.shipping_city, self.shipping_state, self.shipping_zip]):
            return None
        return f"{self.shipping_street}\n{self.shipping_city}, {self.shipping_state} {self.shipping_zip}\n{self.shipping_country}"

    def get_full_billing_address(self):
        """Return formatted billing address"""
        if self.same_billing_shipping:
            return self.get_full_shipping_address()
        if not all([self.billing_street, self.billing_city, self.billing_state, self.billing_zip]):
            return None
        return f"{self.billing_street}\n{self.billing_city}, {self.billing_state} {self.billing_zip}\n{self.billing_country}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Only save profile for existing users (not during creation)
    if not kwargs.get('created', False) and hasattr(instance, 'profile'):
        instance.profile.save()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class VariationType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Color", "Size", "Material"
    display_name = models.CharField(max_length=100)  # e.g., "Choose Color", "Select Size"

    def __str__(self):
        return self.name

class VariationOption(models.Model):
    variation_type = models.ForeignKey(VariationType, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)  # e.g., "Red", "Blue", "Small", "Large"
    display_value = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Ruby Red", "Sapphire Blue"
    color_hex = models.CharField(max_length=7, blank=True, null=True)  # For color variations: #FF0000
    image = models.ImageField(upload_to='variation_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.variation_type.name}: {self.value}"

    class Meta:
        unique_together = ['variation_type', 'value']

class Jewelry(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='jewelry_images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='jewelry_items')
    variation_types = models.ManyToManyField(VariationType, blank=True, related_name='jewelry_items')
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def has_variations(self):
        return self.variation_types.exists()

    @property
    def available_variations(self):
        """Get all possible variation combinations for this jewelry item"""
        return self.product_variations.filter(is_available=True)

class ProductVariation(models.Model):
    jewelry = models.ForeignKey(Jewelry, on_delete=models.CASCADE, related_name='product_variations')
    variation_options = models.ManyToManyField(VariationOption, related_name='product_variations')
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Additional cost for this variation
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='variation_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        options = ", ".join([str(option) for option in self.variation_options.all()])
        return f"{self.jewelry.name} - {options}"

    @property
    def total_price(self):
        """Calculate total price including base price + adjustment"""
        return self.jewelry.price + self.price_adjustment

    def save(self, *args, **kwargs):
        # Save the instance first so it has a primary key
        super().save(*args, **kwargs)

# Signal to handle ProductVariation M2M changes
@receiver(m2m_changed, sender=ProductVariation.variation_options.through)
def handle_variation_options_changed(sender, instance, action, **kwargs):
    """
    Handle SKU generation after variation options are set.
    This runs after M2M relationships are saved, avoiding RecursionError.
    """
    if action == "post_add" or action == "post_remove" or action == "post_clear":
        # Generate SKU if not provided or if it needs updating
        if instance.variation_options.exists():
            options_str = "_".join(sorted([opt.value.lower().replace(" ", "_") for opt in instance.variation_options.all()]))
            new_sku = f"{instance.jewelry.name.lower().replace(' ', '_')}_{options_str}"

            # Only update if SKU is empty or auto-generated (contains jewelry name)
            if not instance.sku or instance.jewelry.name.lower().replace(' ', '_') in instance.sku.lower():
                instance.sku = new_sku
                # Use update() to avoid triggering save() method and potential recursion
                ProductVariation.objects.filter(pk=instance.pk).update(sku=new_sku)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username if self.user else 'Anonymous'}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    jewelry = models.ForeignKey(Jewelry, on_delete=models.CASCADE)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        variation_info = f" ({self.product_variation})" if self.product_variation else ""
        return f"{self.quantity} x {self.jewelry.name}{variation_info} in cart"

    @property
    def unit_price(self):
        """Get the price for a single unit of this cart item"""
        if self.product_variation:
            return self.product_variation.total_price
        return self.jewelry.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    class Meta:
        unique_together = ['cart', 'jewelry', 'product_variation']  # Prevent duplicate items

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    # Buyer Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Shipping Address
    shipping_street = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='USA')

    # Billing Address
    billing_street = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_zip = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100, default='USA')

    # Order Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Square Payment Info
    square_payment_id = models.CharField(max_length=255, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - ${self.total_amount}"

    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    jewelry = models.ForeignKey(Jewelry, on_delete=models.PROTECT)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price snapshot at time of order
    variation_data = models.JSONField(null=True, blank=True)  # Store variation details as JSON for historical reference

    def __str__(self):
        variation_info = f" ({self.product_variation})" if self.product_variation else ""
        return f"{self.quantity} x {self.jewelry.name}{variation_info} in Order #{self.order.id}"

    @property
    def total_price(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Store variation data as JSON for historical reference
        if self.product_variation and not self.variation_data:
            self.variation_data = {
                'variation_options': [
                    {'type': option.variation_type.name, 'value': option.value}
                    for option in self.product_variation.variation_options.all()
                ],
                'price_adjustment': str(self.product_variation.price_adjustment)
            }
        super().save(*args, **kwargs)

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    max_attendees = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['date']

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.date > timezone.now()

    @property
    def is_past(self):
        from django.utils import timezone
        return self.date < timezone.now()