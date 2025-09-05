from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import logging
import requests

# Import shared data manager
try:
    from shared_data_manager import shared_data
    SHARED_DATA_AVAILABLE = True
    print("[INFO] Shared data manager loaded successfully")
except ImportError:
    SHARED_DATA_AVAILABLE = False
    print("[WARNING] shared_data_manager.py not found - using in-memory data")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Simple in-memory storage (replace with database later)
users = {
    'admin': {
        'username': 'admin',
        'email': 'admin@store.com',
        'password_hash': generate_password_hash('admin123'),
        'role': 'admin'
    }
}

store_info = {
    'store_name': 'Your Store',
    'address': '123 Main St',
    'phone': '(555) 123-4567',
    'hours': 'Mon-Fri 8AM-9PM, Sat-Sun 9AM-8PM',
    'greeting_message': 'Thank you for calling our store. How can I help you today?'
}

departments = [
    {'id': 1, 'name': 'Grocery', 'phone_extension': '101', 'description': 'Food items and groceries', 'is_active': True, 'created_at': datetime.now()},
    {'id': 2, 'name': 'Meat & Seafood', 'phone_extension': '102', 'description': 'Fresh meat and seafood', 'is_active': True, 'created_at': datetime.now()},
    {'id': 3, 'name': 'Deli', 'phone_extension': '103', 'description': 'Deli meats and prepared foods', 'is_active': True, 'created_at': datetime.now()},
    {'id': 4, 'name': 'Bakery', 'phone_extension': '104', 'description': 'Fresh bread and pastries', 'is_active': True, 'created_at': datetime.now()},
    {'id': 5, 'name': 'Electronics', 'phone_extension': '105', 'description': 'Electronics and gadgets', 'is_active': True, 'created_at': datetime.now()},
    {'id': 6, 'name': 'Home and Garden', 'phone_extension': '106', 'description': 'Home improvement and garden supplies', 'is_active': True, 'created_at': datetime.now()},
    {'id': 7, 'name': 'Health and Beauty', 'phone_extension': '107', 'description': 'Personal care and beauty products', 'is_active': True, 'created_at': datetime.now()},
    {'id': 8, 'name': 'Pet Supplies', 'phone_extension': '108', 'description': 'Pet food and supplies', 'is_active': True, 'created_at': datetime.now()},
    {'id': 9, 'name': 'Customer Service', 'phone_extension': '109', 'description': 'General customer service', 'is_active': True, 'created_at': datetime.now()}
]

inventory_items = [
    {'id': 1, 'sku': 'GROC-001', 'name': 'Organic Bananas', 'department': 'Grocery', 'price': 2.99, 'quantity': 50, 'location': 'Aisle 1, Shelf A', 'is_featured': True, 'is_active': True},
    {'id': 2, 'sku': 'MEAT-001', 'name': 'Ground Beef', 'department': 'Meat & Seafood', 'price': 8.99, 'quantity': 25, 'location': 'Meat Counter', 'is_featured': False, 'is_active': True},
    {'id': 3, 'sku': 'PET-001', 'name': 'Purina Cat Food', 'department': 'Pet Supplies', 'price': 12.99, 'quantity': 15, 'location': 'Aisle 8, Shelf B', 'is_featured': True, 'is_active': True},
    {'id': 4, 'sku': 'ELEC-001', 'name': 'iPhone Charger', 'department': 'Electronics', 'price': 19.99, 'quantity': 8, 'location': 'Electronics Section', 'is_featured': False, 'is_active': True}
]

coupons = [
    {'id': 1, 'code': 'SAVE20', 'description': '20% off all groceries', 'discount_type': 'percentage', 'discount_value': 20, 'is_store_wide': True, 'is_active': True, 'expires_at': datetime(2024, 12, 31), 'created_at': datetime.now()},
    {'id': 2, 'code': 'WELCOME10', 'description': '10% off first purchase', 'discount_type': 'percentage', 'discount_value': 10, 'is_store_wide': True, 'is_active': True, 'expires_at': datetime(2024, 12, 31), 'created_at': datetime.now()}
]

voice_templates = [
    {'id': 1, 'template_type': 'greeting', 'text_content': 'Thank you for calling our store. How can I help you today?', 'is_active': True, 'variation_number': 1, 'created_at': datetime.now()},
    {'id': 2, 'template_type': 'department_routing', 'text_content': 'I\'ll connect you with the appropriate department right away.', 'is_active': True, 'variation_number': 1, 'created_at': datetime.now()}
]

# Simple user class
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['username']
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data['role']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(users[user_id])
    return None

def sync_with_voice_app(data_type, data, method='PUT'):
    """Sync data with the voice app via API"""
    if not SHARED_DATA_AVAILABLE:
        return True  # Skip if shared data not available
    
    try:
        voice_app_url = "http://localhost:5003"
        api_url = f"{voice_app_url}/api/{data_type}"
        
        response = requests.request(
            method=method,
            url=api_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Successfully synced {data_type} with voice app")
            return True
        else:
            logger.error(f"Failed to sync {data_type} with voice app: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error syncing {data_type} with voice app: {e}")
        return False

# Routes
@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        store_config = shared_data.get_store_info()
        departments_data = shared_data.get_departments()
        inventory_data = shared_data.get_inventory()
        coupons_data = shared_data.get_coupons()
    else:
        store_config = store_info
        departments_data = departments
        inventory_data = inventory_items
        coupons_data = coupons
    
    stats = {
        'total_items': len(inventory_data),
        'low_stock_items': len([item for item in inventory_data if item.get('stock_quantity', item.get('quantity', 0)) < 10]),
        'active_coupons': len([coupon for coupon in coupons_data if coupon['is_active']])
    }
    
    return render_template('dashboard.html',
                         store_config=store_config,
                         departments=departments_data,
                         stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password_hash'], password):
            user = User(users[username])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Store Information Management
@app.route('/store-info', methods=['GET', 'POST'])
@login_required
def store_info_page():
    if request.method == 'POST':
        # Get data from form
        updated_store_info = {
            'name': request.form.get('store_name'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'hours': request.form.get('hours'),
            'greeting_message': request.form.get('greeting_message'),
            'holiday_hours': request.form.get('holiday_hours')
        }
        
        # Update shared data if available
        if SHARED_DATA_AVAILABLE:
            shared_data.update_store_info(updated_store_info)
            # Sync with voice app
            sync_with_voice_app('store-info', updated_store_info)
            
            # Update cache in voice app
            try:
                import requests
                response = requests.post('http://localhost:5003/api/update-cache', 
                                       json={'type': 'dashboard_content'}, timeout=5)
                if response.status_code == 200:
                    print("Cache updated successfully")
                else:
                    print(f"Warning: Could not update cache: {response.status_code}")
            except Exception as e:
                print(f"Warning: Could not update cache: {e}")
        else:
            # Fallback to in-memory data
            global store_info
            store_info.update(updated_store_info)
        
        flash('Store information updated successfully!')
        return redirect(url_for('store_info_page'))
    
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        store_config = shared_data.get_store_info()
    else:
        store_config = store_info
    
    return render_template('store_info.html', store_config=store_config)

@app.route('/api/tts/regenerate', methods=['POST'])
@login_required
def proxy_tts_regenerate():
    """Proxy to voice app to avoid cross-origin issues from dashboard UI."""
    try:
        payload = request.get_json(force=True) or {}
        r = requests.post('http://localhost:5003/api/tts/regenerate', json=payload, timeout=10)
        return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Department Management
@app.route('/departments')
@login_required
def departments_page():
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        departments_data = shared_data.get_departments()
    else:
        departments_data = departments
    
    return render_template('departments.html', departments=departments_data)

@app.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    if request.method == 'POST':
        new_dept = {
            'name': request.form.get('name'),
            'phone_extension': request.form.get('phone_extension'),
            'description': request.form.get('description'),
            'is_active': True
        }
        
        # Add to shared data if available
        if SHARED_DATA_AVAILABLE:
            shared_data.add_department(new_dept)
            # Sync with voice app
            sync_with_voice_app('departments', new_dept, 'POST')
        else:
            # Fallback to in-memory data
            new_dept['id'] = len(departments) + 1
            new_dept['created_at'] = datetime.now()
            departments.append(new_dept)
        
        flash('Department added successfully!')
        return redirect(url_for('departments_page'))
    
    # Get departments for the form
    if SHARED_DATA_AVAILABLE:
        departments_data = shared_data.get_departments()
    else:
        departments_data = departments
    
    return render_template('add_department.html', departments=departments_data)

# Inventory Management
@app.route('/inventory')
@login_required
def inventory_page():
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        inventory_data = shared_data.get_inventory()
        settings = shared_data.get_settings()
    else:
        inventory_data = inventory_items
        settings = {}
    
    return render_template('inventory.html', items=inventory_data, settings=settings)

@app.route('/inventory/integration', methods=['POST'])
@login_required
def save_inventory_integration():
    """Save inventory API integration settings"""
    provider = request.form.get('provider')
    base_url = request.form.get('base_url')
    store_id = request.form.get('store_id')
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')

    if SHARED_DATA_AVAILABLE:
        current = shared_data.get_settings() or {}
        integrations = current.get('integrations', {})
        integrations['inventory'] = {
            'provider': provider,
            'base_url': base_url,
            'store_id': store_id,
            'api_key': api_key,
            'api_secret': api_secret,
        }
        current['integrations'] = integrations
        shared_data.update_settings(current)
        flash('Inventory API settings saved.')
    else:
        flash('Shared data not available; settings not saved.')

    return redirect(url_for('inventory_page'))

@app.route('/inventory/integration/test', methods=['POST'])
@login_required
def test_inventory_integration():
    """Basic connectivity test for inventory API settings"""
    try:
        provider = request.form.get('provider')
        base_url = request.form.get('base_url')
        api_key = request.form.get('api_key')
        # Minimal HEAD/GET to base_url to validate reachability
        if not base_url:
            return jsonify({'ok': False, 'error': 'Missing base URL'}), 400
        r = requests.get(base_url, timeout=5, headers={"Authorization": f"Bearer {api_key}"} if api_key else None)
        return jsonify({'ok': True, 'status': r.status_code})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory_item():
    if request.method == 'POST':
        new_item = {
            'sku': request.form.get('sku'),
            'name': request.form.get('name'),
            'department': request.form.get('department'),
            'price': float(request.form.get('price')),
            'stock_quantity': int(request.form.get('quantity')),
            'location': request.form.get('location'),
            'is_active': True
        }
        
        # Add to shared data if available
        if SHARED_DATA_AVAILABLE:
            shared_data.add_inventory_item(new_item)
            # Sync with voice app
            sync_with_voice_app('inventory', new_item, 'POST')
        else:
            # Fallback to in-memory data
            new_item['id'] = len(inventory_items) + 1
            new_item['quantity'] = new_item.pop('stock_quantity')
            new_item['is_featured'] = bool(request.form.get('is_featured'))
            inventory_items.append(new_item)
        
        flash('Inventory item added successfully!')
        return redirect(url_for('inventory_page'))
    
    # Get departments for the form
    if SHARED_DATA_AVAILABLE:
        departments_data = shared_data.get_departments()
    else:
        departments_data = departments
    
    return render_template('add_inventory_item.html', departments=departments_data)

# Coupon Management
@app.route('/coupons')
@login_required
def coupons_page():
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        coupons_data = shared_data.get_coupons()
        dialogue_data = shared_data.get_dialogue_templates()
    else:
        coupons_data = coupons
        dialogue_data = {}
    
    return render_template('coupons.html', coupons=coupons_data, dialogue_templates=dialogue_data, now=datetime.now())

@app.route('/coupons/add', methods=['GET', 'POST'])
@login_required
def add_coupon():
    if request.method == 'POST':
        new_coupon = {
            'code': request.form.get('code'),
            'description': request.form.get('description'),
            'discount_type': request.form.get('discount_type'),
            'discount_value': float(request.form.get('discount_value')),
            'is_store_wide': bool(request.form.get('is_store_wide')),
            'is_active': bool(request.form.get('is_active')),
            'expires_at': request.form.get('expires_at') + 'T23:59:59'  # Add time to date
        }
        
        # Add to shared data if available
        if SHARED_DATA_AVAILABLE:
            shared_data.add_coupon(new_coupon)
            # Sync with voice app
            sync_with_voice_app('coupons', new_coupon, 'POST')
        else:
            # Fallback to in-memory data
            new_coupon['id'] = len(coupons) + 1
            new_coupon['expires_at'] = datetime.strptime(request.form.get('expires_at'), '%Y-%m-%d')
            new_coupon['created_at'] = datetime.now()
            coupons.append(new_coupon)
        
        flash('Coupon added successfully!')
        return redirect(url_for('coupons_page'))
    
    return render_template('add_coupon.html')

# Voice Templates
@app.route('/voice-templates')
@login_required
def voice_templates_page():
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        templates_data = shared_data.get_voice_templates()
    else:
        templates_data = voice_templates
    
    return render_template('voice_templates.html', templates=templates_data)

@app.route('/voice-templates/generate', methods=['POST'])
@login_required
def generate_voice_template():
    template_type = request.form.get('template_type')
    text_content = request.form.get('text_content')
    
    new_template = {
        'template_type': template_type,
        'text_content': text_content,
        'is_active': True,
        'variation_number': 1
    }
    
    # Add to shared data if available
    if SHARED_DATA_AVAILABLE:
        shared_data.add_voice_template(new_template)
        # Sync with voice app
        sync_with_voice_app('voice-templates', new_template, 'POST')
    else:
        # Fallback to in-memory data
        new_template['id'] = len(voice_templates) + 1
        new_template['created_at'] = datetime.now()
        voice_templates.append(new_template)
    
    flash('Voice template created! (Audio generation pending)')
    return redirect(url_for('voice_templates_page'))

# Dialogue Templates
@app.route('/dialogue-templates')
@login_required
def dialogue_templates_page():
    # Get data from shared data if available
    if SHARED_DATA_AVAILABLE:
        dialogue_data = shared_data.get_dialogue_templates()
    else:
        dialogue_data = {}

    # Remove unused keys (General → Greet) since greeting lives in Store Info
    if 'general' in dialogue_data:
        dialogue_data['general'].pop('greet', None)

    # Define preferred ordering per category (most/first used first)
    preferred_order = {
        'general': [
            'anything_else', 'confirm_prefix', 'yes_no', 'reask', 'reask_cap',
            'connecting_operator', 'timeout', 'thanks_calling', 'goodbye',
            'err_global', 'err_confirm', 'no_record', 'error_goodbye', 'error_processing', 'no_speech', 'hit_snag'
        ],
        'pharmacy': [
            'pharmacy_greeting', 'status_check_prompt', 'refill_prompt',
            'prescription_ready', 'prescription_processing', 'prescription_delayed',
            'prescription_out_of_stock', 'no_prescriptions_found', 'no_rx_found',
            'transfer_general', 'transfer_from_pharmacy'
        ],
        'coupons': [
            'coupons_available', 'sms_consent_prompt', 'sms_body',
            'sms_consent_thanks_yes', 'sms_consent_thanks_no',
            'department_coupons_intro', 'no_department_coupons',
            'no_specific_coupons', 'no_coupons_for_item', 'help_find_coupons',
            'coupon_replay_prompt', 'coupon_replay_thanks'
        ],
        'spanish': [
            'greet', 'confirm_prefix', 'yes_no', 'reask', 'reask_cap', 'connecting_operator', 'err_global', 'err_confirm', 'no_record'
        ]
    }

    # Build an ordered view for the template: {category: [(key, text), ...]}
    ordered_dialogue = {}
    for category, templates in dialogue_data.items():
        order = preferred_order.get(category, [])
        # keys in preferred order first, then any remaining keys alphabetically
        seen = set()
        ordered_items = []
        for k in order:
            if k in templates:
                ordered_items.append((k, templates[k]))
                seen.add(k)
        for k in sorted([kk for kk in templates.keys() if kk not in seen]):
            ordered_items.append((k, templates[k]))
        ordered_dialogue[category] = ordered_items

    return render_template('dialogue_templates.html', dialogue_templates=ordered_dialogue)

@app.route('/dialogue-templates/update', methods=['POST'])
@login_required
def update_dialogue_template():
    category = request.form.get('category')
    key = request.form.get('key')
    text = request.form.get('text')
    
    if SHARED_DATA_AVAILABLE:
        shared_data.update_dialogue_template(category, key, text)
        
        # Update cache in voice app
        try:
            import requests
            response = requests.post('http://localhost:5003/api/update-cache', timeout=5)
            if response.status_code == 200:
                print("Cache updated successfully")
            else:
                print(f"Warning: Could not update cache: {response.status_code}")
        except Exception as e:
            print(f"Warning: Could not update cache: {e}")
        
        # Friendlier message when updating coupon SMS body
        if category == 'coupons' and key == 'sms_body':
            flash('Coupon message updated successfully!')
        else:
            flash(f'Dialogue template "{key}" updated successfully!')
    else:
        flash('Shared data not available')
    
    # If editing coupon sms from coupons page, bounce back there for quick iteration
    if category == 'coupons' and key == 'sms_body':
        return redirect(url_for('coupons_page'))
    return redirect(url_for('dialogue_templates_page'))

# Usage Monitoring
@app.route('/usage-monitoring')
@login_required
def usage_monitoring():
    # Get usage data from voice app if available
    try:
        response = requests.get('http://localhost:5003/api/usage', timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            
            # Transform API response to match template expectations
            usage_data = {
                "daily_summary": {
                    "total_credits": api_data.get("credit_tracker", {}).get("total_credits", 0),
                    "active_calls": api_data.get("credit_tracker", {}).get("active_calls", 0),
                    "date": api_data.get("credit_tracker", {}).get("date", "Unknown")
                },
                "service_breakdown": api_data.get("service_breakdown", {}),
                "cache_stats": {
                    "total_files": api_data.get("cache_stats", {}).get("total_cached_files", 0),
                    "cache_hits": api_data.get("cache_stats", {}).get("cache_hits", 0),
                    "cache_misses": api_data.get("cache_stats", {}).get("cache_misses", 0),
                    "hit_rate_percent": api_data.get("cache_stats", {}).get("hit_rate_percent", 0),
                    "tts_calls": api_data.get("cache_stats", {}).get("tts_calls", 0),
                    "total_chars_synthesized": api_data.get("cache_stats", {}).get("total_chars_synthesized", 0),
                    "cache_dir": api_data.get("cache_stats", {}).get("cache_dir", "static/tts_cache")
                },
                "elevenlabs_config": {
                    "api_key_set": api_data.get("elevenlabs", {}).get("api_key_set", False),
                    "api_key_length": api_data.get("elevenlabs", {}).get("api_key_length", 0),
                    "voice_id": api_data.get("elevenlabs", {}).get("voice_id", "Not set"),
                    "subscription": api_data.get("elevenlabs", {}).get("subscription", {}),
                    "error": api_data.get("elevenlabs", {}).get("error", None)
                }
            }
        else:
            usage_data = {"error": "Could not fetch usage data"}
    except Exception as e:
        usage_data = {"error": f"Connection error: {str(e)}"}
    
    return render_template('usage_monitoring.html', usage_data=usage_data)

# API Endpoints for AJAX calls
@app.route('/api/inventory/search')
@login_required
def search_inventory():
    query = request.args.get('q', '').lower()
    results = []
    
    for item in inventory_items:
        if query in item['name'].lower() or query in item['sku'].lower():
            results.append(item)
    
    return jsonify(results[:10])

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@login_required
def update_inventory_item(item_id):
    data = request.get_json()
    
    for item in inventory_items:
        if item['id'] == item_id:
            item['quantity'] = data.get('quantity', item['quantity'])
            item['price'] = data.get('price', item['price'])
            item['location'] = data.get('location', item['location'])
            break
    
    return jsonify({'success': True})

# Analytics
@app.route('/analytics')
@login_required
def analytics():
    # Pull live usage metrics from voice app
    usage_data = {}
    try:
        r = requests.get('http://localhost:5003/api/usage', timeout=5)
        if r.status_code == 200:
            usage_data = r.json()
    except Exception as e:
        usage_data = {"error": str(e)}
    return render_template('analytics.html', usage=usage_data)

# Proxies for hide/unhide to voice app
@app.route('/api/analytics/items/hide', methods=['POST'])
@login_required
def proxy_hide_item():
    try:
        name = request.json.get('name', '') if request.is_json else (request.form.get('name', '') )
        r = requests.post('http://localhost:5003/api/items/hide', json={'name': name}, timeout=5)
        return (r.text, r.status_code, r.headers.items())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/items/unhide', methods=['POST'])
@login_required
def proxy_unhide_item():
    try:
        name = request.json.get('name', '') if request.is_json else (request.form.get('name', '') )
        r = requests.post('http://localhost:5003/api/items/unhide', json={'name': name}, timeout=5)
        return (r.text, r.status_code, r.headers.items())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Staff Management
@app.route('/staff', endpoint='staff')
@login_required
def staff_page():
    staff_list = shared_data.get_staff() if SHARED_DATA_AVAILABLE else []
    return render_template('staff.html', staff_list=staff_list)

@app.route('/staff/add', methods=['POST'])
@login_required
def staff_add():
    data = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'department': request.form.get('department'),
        'role': request.form.get('role'),
        'is_active': bool(request.form.get('is_active'))
    }
    if SHARED_DATA_AVAILABLE:
        shared_data.add_staff(data)
        flash('Staff member added.')
    else:
        flash('Shared data not available; could not save staff.')
    return redirect(url_for('staff'))

@app.route('/staff/<int:staff_id>/update', methods=['POST'])
@login_required
def staff_update(staff_id: int):
    updates = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'department': request.form.get('department'),
        'role': request.form.get('role'),
        'is_active': bool(request.form.get('is_active'))
    }
    ok = shared_data.update_staff(staff_id, updates) if SHARED_DATA_AVAILABLE else False
    flash('Staff member updated.' if ok else 'Could not update staff member.')
    return redirect(url_for('staff'))

@app.route('/staff/<int:staff_id>/delete', methods=['POST'])
@login_required
def staff_delete(staff_id: int):
    ok = shared_data.delete_staff(staff_id) if SHARED_DATA_AVAILABLE else False
    flash('Staff member removed.' if ok else 'Could not remove staff member.')
    return redirect(url_for('staff'))

# Settings
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, port=5004)
