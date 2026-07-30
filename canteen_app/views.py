import os
## Only import joblib once at the top
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .utils.excel_io import load_menu_df, write_menu_df
from .utils.combo import compute_utilities, generate_smart_combos
from .models import MenuItem, Order, OrderItem
from django.http import JsonResponse
import joblib
import json
from django.views.decorators.csrf import csrf_exempt

# Folder where your ML models are stored
ARTIFACT_DIR = os.path.join(settings.BASE_DIR, 'canteen_app', 'artifacts')

# Regression model
PREF_REG_PATH = os.path.join(ARTIFACT_DIR, 'pref_reg.joblib')
try:
    pref_reg = joblib.load(PREF_REG_PATH)
except Exception as e:
    pref_reg = None
    print(f"Could not load ML model: {e}")

# Optional: menu cache or other models
MENU_CACHE_PATH = os.path.join(ARTIFACT_DIR, 'menu_with_preds.pkl')
try:
    menu_cache = joblib.load(MENU_CACHE_PATH)
except Exception as e:
    menu_cache = None
    print(f"Could not load menu cache: {e}")



ART_PATH = joblib  # we use joblib for artifacts if saved

def home(request):
    return render(request, 'canteen_app/home.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.roll_no = form.cleaned_data['roll_no']
            user.save()
            login(request, user)
            return redirect('order')
    else:
        form = RegisterForm()
    return render(request, 'canteen_app/register.html', {'form':form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('order')
        else:
            messages.error(request, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    return render(request, 'canteen_app/login.html', {'form':form})

def logout_view(request):
    logout(request)
    return redirect('home')

def order_page(request):
    # load menu for direct display
    qs = MenuItem.objects.filter(active=True)
    menu = qs.order_by('category__name','name')
    return render(request, 'canteen_app/order.html', {'menu':menu})

# API endpoints
def api_recommend(request):
    # Debug print removed (was causing undefined variable error)
    typ = request.GET.get('type', 'All')
    budget = float(request.GET.get('budget', 100))
    meal_type = request.GET.get('meal_type', None)
    max_items = int(request.GET.get('max_items', 4))

    df = load_menu_df()
    print("Menu loaded, total items:", len(df))
    if df.empty:
        return JsonResponse({'combos': [], 'message': 'Menu is empty.'})

    combos = generate_smart_combos(df, budget=budget, prefer_type=typ, meal_type=meal_type, max_items=max_items)
    print(f"Generated {len(combos)} combos (meal_type={meal_type})")
    # Fallback: if no combos found and meal_type is not None/All, retry with meal_type=None
    if not combos and meal_type and str(meal_type).strip().lower() not in ['none', '', 'all']:
        combos = generate_smart_combos(df, budget=budget, prefer_type=typ, meal_type=None, max_items=max_items)
        print(f"Fallback: Generated {len(combos)} combos (meal_type=None)")
    if not combos:
        return JsonResponse({'combos': [], 'message': 'No combos found for the given criteria.'})

    combos_out = []
    for combo in combos:
        combo_items = []
        for item in combo['items']:
            combo_items.append({
                'ItemID': item.get('ItemID', ''),
                'ItemName': item.get('ItemName', ''),
                'Price': item.get('Price', 0),
                'Type': item.get('Type', ''),
            })
        combos_out.append({
            'items': combo_items,
            'total_price': combo.get('total_price', 0),
            'total_utility': combo.get('total_utility', 0),
            'n_items': combo.get('n_items', 0),
            'n_nonveg': combo.get('n_nonveg', 0),
            'n_veg': combo.get('n_veg', 0)
        })
    return JsonResponse({'combos': combos_out})


@csrf_exempt
def api_place_order(request):
    if request.method != 'POST':
        return JsonResponse({'error':'POST required'}, status=400)
    payload = json.loads(request.body)
    user = request.user if request.user.is_authenticated else None
    if not user:
        return JsonResponse({'error':'auth required'}, status=401)
    items = payload.get('items', [])
    if not items:
        return JsonResponse({'error':'no items'}, status=400)

    # create order and update DB preference & Excel
    total = 0.0
    order = Order.objects.create(user=user, total_price=0.0, paid=True)
    for iid in items:
        try:
            mi = MenuItem.objects.get(itemid=iid)
            OrderItem.objects.create(order=order, item=mi, qty=1)
            total += mi.price
            # increment preference_score (simple +1)
            mi.preference_score += 1.0
            mi.save()
        except MenuItem.DoesNotExist:
            pass

    order.total_price = total
    order.save()

    # update Excel: load DataFrame, bump PreferenceScore for ordered ItemIDs, save
    #df = load_menu_df()
    #df.loc[df['ItemID'].isin(items), 'PreferenceScore'] = df.loc[df['ItemID'].isin(items), 'PreferenceScore'] + 1
    #write_menu_df(df)
    # recompute utilities and optionally save menu cache
    #df2 = compute_utilities(df)
    #joblib.dump(df2, 'canteen_app/artifacts/menu_with_preds.pkl')

    return JsonResponse({'status':'ok', 'order_id': order.id, 'total': total})
