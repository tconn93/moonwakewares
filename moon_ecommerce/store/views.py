from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Jewelry, Cart, CartItem, Order, OrderItem, Event
from django.contrib import messages
from django.conf import settings
from square import Square
import uuid
import logging

logger = logging.getLogger(__name__)

# Existing views (home, product_list, product_detail)
def home(request):
    return render(request, 'store/home.html')

def product_list(request):
    jewelry_items = Jewelry.objects.all()
    return render(request, 'store/product_list.html', {'jewelry_items': jewelry_items})

def product_detail(request, pk):
    jewelry = get_object_or_404(Jewelry, pk=pk)
    return render(request, 'store/product_detail.html', {'jewelry': jewelry})

# Helper function to get or create a cart
def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    # For anonymous users, use session
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

# View cart
def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})

# Add item to cart
def add_to_cart(request, jewelry_id):
    jewelry = get_object_or_404(Jewelry, id=jewelry_id)
    cart = get_cart(request)
    
    # Check if the item is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, jewelry=jewelry)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{jewelry.name} added to cart!")
    return redirect('cart_detail')

# Update cart item quantity
def update_cart(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=get_cart(request))
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f"Updated {cart_item.jewelry.name} quantity.")
        else:
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.jewelry.name} from cart.")
    return redirect('cart_detail')

# Remove item from cart
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=get_cart(request))
    cart_item.delete()
    messages.success(request, f"Removed {cart_item.jewelry.name} from cart.")
    return redirect('cart_detail')

# Checkout views
@login_required
def checkout(request):
    """Display checkout form"""
    cart = get_cart(request)
    cart_items = cart.cartitem_set.all()

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')

    # Pre-fill form with user's profile data
    profile = request.user.profile
    context = {
        'cart': cart,
        'user_email': request.user.email,
        'profile': profile,
        'SQUARE_APPLICATION_ID': settings.SQUARE_APPLICATION_ID,
        'SQUARE_LOCATION_ID': settings.SQUARE_LOCATION_ID,
        'SQUARE_ENVIRONMENT': settings.SQUARE_ENVIRONMENT,
    }
    return render(request, 'store/checkout.html', context)

@login_required
def process_payment(request):
    """Process Square payment and create order"""
    if request.method != 'POST':
        return redirect('checkout')

    cart = get_cart(request)
    cart_items = cart.cartitem_set.all()

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('cart_detail')

    # Get form data
    full_name = request.POST.get('full_name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')

    shipping_street = request.POST.get('shipping_street')
    shipping_city = request.POST.get('shipping_city')
    shipping_state = request.POST.get('shipping_state')
    shipping_zip = request.POST.get('shipping_zip')
    shipping_country = request.POST.get('shipping_country', 'USA')

    billing_street = request.POST.get('billing_street')
    billing_city = request.POST.get('billing_city')
    billing_state = request.POST.get('billing_state')
    billing_zip = request.POST.get('billing_zip')
    billing_country = request.POST.get('billing_country', 'USA')

    # Save/update user profile
    profile = request.user.profile
    profile.full_name = full_name
    profile.phone = phone
    profile.shipping_street = shipping_street
    profile.shipping_city = shipping_city
    profile.shipping_state = shipping_state
    profile.shipping_zip = shipping_zip
    profile.shipping_country = shipping_country
    profile.billing_street = billing_street
    profile.billing_city = billing_city
    profile.billing_state = billing_state
    profile.billing_zip = billing_zip
    profile.billing_country = billing_country
    profile.save()

    source_id = request.POST.get('source_id')  # This comes from Square Web Payments SDK

    # Calculate total
    total_amount = cart.total_price

    # Initialize Square client
    client = Square(
        token=settings.SQUARE_ACCESS_TOKEN,
    )

    try:
        # Create payment with Square
        result = client.payments.create(
       
                source_id= source_id,
                idempotency_key= str(uuid.uuid4()),
                amount_money= {
                    "amount": int(total_amount * 100),  # Square uses cents
                    "currency": "USD"
                },
                location_id= settings.SQUARE_LOCATION_ID,
          
        )

        if result.is_success():
            payment_response = result.body
            payment_id = payment_response['payment']['id']

            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                email=email,
                phone=phone,
                shipping_street=shipping_street,
                shipping_city=shipping_city,
                shipping_state=shipping_state,
                shipping_zip=shipping_zip,
                shipping_country=shipping_country,
                billing_street=billing_street,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_zip=billing_zip,
                billing_country=billing_country,
                total_amount=total_amount,
                square_payment_id=payment_id,
                status='completed'
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    jewelry=cart_item.jewelry,
                    quantity=cart_item.quantity,
                    price=cart_item.jewelry.price
                )

            # Clear cart
            cart_items.delete()

            messages.success(request, f"Payment successful! Order #{order.id} has been placed.")
            return redirect('order_confirmation', order_id=order.id)

        else:
            # Payment failed
            errors = result.errors
            logger.error(f"Square payment failed: {errors}")
            messages.error(request, "Payment failed. Please try again or use a different payment method.")
            return redirect('checkout')

    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        messages.error(request, "An error occurred while processing your payment. Please try again.")
        return redirect('checkout')

@login_required
def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__jewelry')
    return render(request, 'store/order_history.html', {'orders': orders})

# Custom orders view
def custom_orders(request):
    """Display custom orders page with link to JotForm"""
    return render(request, 'store/custom_orders.html')

# User profile view
@login_required
def user_profile(request):
    """User profile management"""
    if request.method == 'POST':
        # Update user profile
        profile = request.user.profile
        profile.full_name = request.POST.get('full_name', '')
        profile.phone = request.POST.get('phone', '')
        profile.shipping_street = request.POST.get('shipping_street', '')
        profile.shipping_city = request.POST.get('shipping_city', '')
        profile.shipping_state = request.POST.get('shipping_state', '')
        profile.shipping_zip = request.POST.get('shipping_zip', '')
        profile.shipping_country = request.POST.get('shipping_country', 'USA')
        profile.billing_street = request.POST.get('billing_street', '')
        profile.billing_city = request.POST.get('billing_city', '')
        profile.billing_state = request.POST.get('billing_state', '')
        profile.billing_zip = request.POST.get('billing_zip', '')
        profile.billing_country = request.POST.get('billing_country', 'USA')
        profile.same_billing_shipping = request.POST.get('same_billing_shipping') == 'on'
        profile.save()

        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('user_profile')

    return render(request, 'store/user_profile.html', {
        'profile': request.user.profile
    })

# User registration view
def signup(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f"Welcome {username}! Your account has been created.")

            # Redirect to 'next' parameter if available, otherwise go to home
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

# Events view
def events(request):
    """Display all active events"""
    from django.utils import timezone
    events_list = Event.objects.filter(is_active=True).order_by('date')
    upcoming_events = events_list.filter(date__gte=timezone.now())
    past_events = events_list.filter(date__lt=timezone.now())

    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'store/events.html', context)