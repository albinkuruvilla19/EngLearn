import json
from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from .models import *
from django.contrib import messages
from .forms import ProductForm,CustomUserForm,SearchForm
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F, Sum
from django.db import transaction

# Create your views here.
def home(request):
    category = Category.objects.all()[:6]
    products = Products.objects.filter(bestseller=1,status=0)
    allproducts = Products.objects.filter(status=0)
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data['query']
        if query:
            allproducts = allproducts.filter(name__icontains=query)
    return render(request,"index.html",{"category":category,"products":products,"allproducts":allproducts,'search_form': search_form})


def shop(request):
    return render(request,"shop.html")
def about(request):
    return render(request,"about.html")
def contact(request):
    return render(request,"contact.html")

def account(request):
    return render(request,"account.html")

def login(request):
    return render(request,"login.html")

def collections(request):
    category = Category.objects.filter(status=0)
    return render(request,"category.html",{"category":category})

def collectionsview(request,name):
    if(Category.objects.filter(name=name,status=0)):
        products = Products.objects.filter(category__name = name)
        return render(request,'collectionsview.html',{"products":products,"category_name":name})
    else:
        messages.warning(request,"No such category found")
        return redirect('collections')
    
def productsview(request,cname,pname):
    if(Category.objects.filter(name=cname,status=0)):
        if(Products.objects.filter(name=pname,status=0)):
            products = Products.objects.filter(name=pname,status=0).first()
            return render(request,'product_details.html',{"products":products})
        else:
            messages.error(request,"No product found")
            return redirect("collections")
    else:
        messages.error(request,"No such category found")
        return redirect("collections")

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def view(request):
    products = Products.objects.all()
    return render(request, 'view.html', {'products': products})

    

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            
            # Redirect to a project list view
            return redirect('view')
    
    form = ProductForm()
    return render(request,'addproduct.html',{'form': form})

def edit_product(request, product_id):
    product = Products.objects.get(id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('view')  
    else:
        form = ProductForm(instance=product)
    return render(request, 'update.html', {'form': form})


def delete_product(request, product_id):
    product = Products.objects.get(id=product_id)  
    messages.success(request,"deleted")
    product.delete()
    return redirect('view')

def register(request):
    form = CustomUserForm
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration success. Login now!!!")
            return redirect('/login')
    return render(request,"register.html",{"form":form})

def loginpage(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=name, password=pwd)

        if user is not None:
            auth_login(request, user)
            
            if user.is_superuser:
                messages.success(request, "Superuser logged in successfully")
                return redirect('view')
            else:
                messages.success(request, "Logged in successfully")
                return redirect("/")
        else:
            messages.error(request, "Invalid Username or password")
            return redirect('login')

    return render(request, "login.html")

def logout_view(request):
    # Use the built-in logout function to log the user out
    logout(request)
    return redirect('login')  # Redirect to your login page or any other desired page after logout

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                auth_login(request,user)
                messages.success(request, 'You have successfully logged in as a superuser.')
                return redirect('view')  # Redirect to the admin dashboard
            else:
                messages.error(request, 'You are not authorized to access this page.')
        else:
            messages.error(request, 'Invalid login credentials.')

    return render(request, 'admin_login.html') 

def add_to_cart(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.load(request)
            products_qty = data['product_qty']
            products_id = data['pid']
            # user_id = request.user.id
            product_status = Products.objects.get(id=products_id)
            if product_status:
                if Cart.objects.filter(user=request.user, products_id=products_id, checked_out=False).exists():
                    return JsonResponse({'status':'Product Already in Cart'},status = 200)
                else:
                    if product_status.quantity >= products_qty:
                        Cart.objects.create(user=request.user, products_id=products_id, product_quantity=products_qty)
                        return JsonResponse({'status':'Product Added successsfully'},status = 200)
                    else:
                        return JsonResponse({'status':'Out of stock'},status = 200)
        else:
            return JsonResponse({'status':'Login to add cart'},status =200)
    else:
        return JsonResponse({'status':'Invalid Access'},status =200)
    
def viewcart(request):
    if request.user.is_authenticated:
         cart = Cart.objects.filter(user=request.user, checked_out=False)
         return render(request, 'cart.html', {"cart": cart})
    else:
        return redirect("home")
    
def removecart(request,cid):
    cart = Cart.objects.get(id=cid)  
    messages.success(request,"deleted")
    cart.delete()
    return redirect('cart')

# views.py
from .forms import CheckoutForm
from .models import Cart, Checkout

# views.py
from django.shortcuts import render
from .models import Cart
from .forms import CheckoutForm
@transaction.atomic
def checkout(request):
    # Fetch the cart items for the user
    cart_items = Cart.objects.filter(user=request.user, checked_out=False)

    # Update subtotal for each item based on the current product price
    for item in cart_items:
        item.subtotal = item.products.selling_price * item.product_quantity
        item.save()

    # Calculate total cart price using Django's aggregate function
    total_cart_price = cart_items.aggregate(total=Sum(F('products__selling_price') * F('product_quantity'), output_field=models.FloatField()))['total']

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            address = form.cleaned_data['address']
            phone_number = form.cleaned_data['phone_number']

            # Save checkout information
            checkout = Checkout.objects.create(
                user=request.user,
                name=name,
                address=address,
                phone_number=phone_number
            )
            for item in cart_items:
                product = item.products
                product.quantity -= item.product_quantity
                product.save()
            # Mark items in the cart as checked out
            cart_items.update(checked_out=True)

            return render(request, 'checkout_success.html', {'checkout': checkout})
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'cart_items': cart_items, 'total_cart_price': total_cart_price})


def order_history(request):
    # Fetch all checkouts for the user
    order_history = Checkout.objects.filter(user=request.user).order_by('-created_at')

    # Fetch related cart items for each order
    for order in order_history:
        order.cart_items = Cart.objects.filter(user=request.user, checked_out=True, created_at__lte=order.created_at)

    return render(request, 'order_history.html', {'order_history': order_history}) 

from django.shortcuts import render
from .models import Products, Category

def product_search(request):
    query = request.GET.get('q')  # Get the search query from the URL parameter 'q'

    if query:
        # Perform a case-insensitive search on the Product model fields
        results = Products.objects.filter(
            name__icontains=query) | Products.objects.filter(
            seller__icontains=query) | Products.objects.filter(
            category__name__icontains=query)  # Add more fields as needed

        context = {'results': results, 'query': query}
    else:
        # If no query is provided, display all products
        results = Products.objects.all()
        context = {'results': results, 'query': ''}

    return render(request, 'product_search_results.html', context)
