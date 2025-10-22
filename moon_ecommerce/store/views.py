from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Jewelry, Cart, CartItem
from django.contrib import messages

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