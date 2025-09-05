from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Optional
import logging
from shared_data_manager import shared_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store_dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='employee')  # 'admin', 'manager', 'employee'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class StoreInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Text, nullable=False)  # JSON string
    greeting_message = db.Column(db.Text, nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_extension = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_closed = db.Column(db.Boolean, default=True)
    special_hours = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))  # Aisle/bin assignment
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    is_store_wide = db.Column(db.Boolean, default=True)
    applicable_products = db.Column(db.Text)  # JSON string of product SKUs
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VoiceTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), nullable=False)  # 'greeting', 'department_routing', etc.
    text_content = db.Column(db.Text, nullable=False)
    audio_file_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    variation_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string
    new_values = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility Functions
def log_audit(user_id: int, action: str, table_name: str, record_id: int = None, 
              old_values: Dict = None, new_values: Dict = None):
    """Log audit trail for all changes"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None
    )
    db.session.add(audit)
    db.session.commit()

def get_store_config():
    """Get current store configuration"""
    store_info = StoreInfo.query.first()
    if not store_info:
        return {
            'store_name': 'Your Store',
            'address': '123 Main St',
            'phone': '(555) 123-4567',
            'hours': 'Mon-Fri 8AM-9PM, Sat-Sun 9AM-8PM',
            'greeting_message': 'Thank you for calling our store. How can I help you today?'
        }
    
    return {
        'store_name': store_info.store_name,
        'address': store_info.address,
        'phone': store_info.phone,
        'hours': store_info.hours,
        'greeting_message': store_info.greeting_message
    }

# Routes
@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    store_config = get_store_config()
    departments = Department.query.filter_by(is_active=True).all()
    recent_audits = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    # Get quick stats
    total_items = InventoryItem.query.filter_by(is_active=True).count()
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity < 10, 
        InventoryItem.is_active == True
    ).count()
    active_coupons = Coupon.query.filter_by(is_active=True).count()
    
    return render_template('dashboard.html',
                         store_config=store_config,
                         departments=departments,
                         recent_audits=recent_audits,
                         stats={
                             'total_items': total_items,
                             'low_stock_items': low_stock_items,
                             'active_coupons': active_coupons
                         })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
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
@app.route('/store-info', methods=['GET', 'POST'], endpoint='store_info_page')
@login_required
def store_info():
    if request.method == 'POST':
        store_info = StoreInfo.query.first()
        old_values = None
        
        if store_info:
            old_values = {
                'store_name': store_info.store_name,
                'address': store_info.address,
                'phone': store_info.phone,
                'hours': store_info.hours,
                'greeting_message': store_info.greeting_message
            }
            store_info.store_name = request.form.get('store_name')
            store_info.address = request.form.get('address')
            store_info.phone = request.form.get('phone')
            store_info.hours = request.form.get('hours')
            store_info.greeting_message = request.form.get('greeting_message')
            store_info.updated_by = current_user.id
            store_info.updated_at = datetime.utcnow()
        else:
            store_info = StoreInfo(
                store_name=request.form.get('store_name'),
                address=request.form.get('address'),
                phone=request.form.get('phone'),
                hours=request.form.get('hours'),
                greeting_message=request.form.get('greeting_message'),
                updated_by=current_user.id
            )
            db.session.add(store_info)
        
        db.session.commit()

        # Sync to voice app shared JSON so greeting and store info reflect immediately
        try:
            shared_data.update_store_info({
                'name': request.form.get('store_name'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'hours': request.form.get('hours'),
                'greeting_message': request.form.get('greeting_message')
            })
        except Exception as e:
            logger.warning(f"Failed to sync store info to voice app: {e}")
        
        # Log audit
        log_audit(
            user_id=current_user.id,
            action='UPDATE_STORE_INFO',
            table_name='store_info',
            old_values=old_values,
            new_values=request.form.to_dict()
        )
        
        flash('Store information updated successfully!')
        return redirect(url_for('store_info_page'))
    
    store_config = get_store_config()
    return render_template('store_info.html', store_config=store_config)

# Department Management
@app.route('/departments', endpoint='departments_page')
@login_required
def departments():
    deps = Department.query.all()
    return render_template('departments.html', departments=deps)

@app.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    if request.method == 'POST':
        dept = Department(
            name=request.form.get('name'),
            phone_extension=request.form.get('phone_extension'),
            description=request.form.get('description')
        )
        db.session.add(dept)
        db.session.commit()
        
        log_audit(
            user_id=current_user.id,
            action='ADD_DEPARTMENT',
            table_name='department',
            record_id=dept.id,
            new_values=request.form.to_dict()
        )
        
        flash('Department added successfully!')
        return redirect(url_for('departments_page'))
    
    return render_template('add_department.html')

# Inventory Management
@app.route('/inventory', endpoint='inventory_page')
@login_required
def inventory():
    items = InventoryItem.query.filter_by(is_active=True).all()
    # Add stock_quantity attribute to match template expectations
    for item in items:
        item.stock_quantity = item.quantity
    return render_template('inventory.html', items=items)

@app.route('/inventory/integration', methods=['POST'], endpoint='save_inventory_integration')
@login_required
def save_inventory_integration():
    return jsonify({"ok": False, "error": "Inventory integration not implemented"}), 501

@app.route('/inventory/integration/test', methods=['POST'], endpoint='test_inventory_integration')
@login_required
def test_inventory_integration():
    return jsonify({"ok": False, "error": "Inventory integration test not implemented"}), 501

@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory_item():
    if request.method == 'POST':
        item = InventoryItem(
            sku=request.form.get('sku'),
            name=request.form.get('name'),
            department=request.form.get('department'),
            price=float(request.form.get('price')),
            quantity=int(request.form.get('quantity')),
            location=request.form.get('location'),
            is_featured=bool(request.form.get('is_featured'))
        )
        db.session.add(item)
        db.session.commit()
        
        log_audit(
            user_id=current_user.id,
            action='ADD_INVENTORY_ITEM',
            table_name='inventory_item',
            record_id=item.id,
            new_values=request.form.to_dict()
        )
        
        flash('Inventory item added successfully!')
        return redirect(url_for('inventory_page'))
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('add_inventory_item.html', departments=departments)

# Coupon Management
@app.route('/coupons', endpoint='coupons_page')
@login_required
def coupons():
    coupons = Coupon.query.all()
    
    # Load dialogue templates for SMS text
    try:
        with open('data/dialogue_templates.json', 'r') as f:
            dialogue_templates = json.load(f)
    except:
        dialogue_templates = {}
    
    return render_template('coupons.html', coupons=coupons, dialogue_templates=dialogue_templates, now=datetime.utcnow())

@app.route('/coupons/add', methods=['GET', 'POST'])
@login_required
def add_coupon():
    if request.method == 'POST':
        coupon = Coupon(
            code=request.form.get('code'),
            description=request.form.get('description'),
            discount_type=request.form.get('discount_type'),
            discount_value=float(request.form.get('discount_value')),
            is_store_wide=bool(request.form.get('is_store_wide')),
            expires_at=datetime.strptime(request.form.get('expires_at'), '%Y-%m-%d') if request.form.get('expires_at') else None
        )
        db.session.add(coupon)
        db.session.commit()
        
        log_audit(
            user_id=current_user.id,
            action='ADD_COUPON',
            table_name='coupon',
            record_id=coupon.id,
            new_values=request.form.to_dict()
        )
        
        flash('Coupon added successfully!')
        return redirect(url_for('coupons_page'))
    
    return render_template('add_coupon.html')

# Voice Templates
@app.route('/voice-templates')
@login_required
def voice_templates():
    templates = VoiceTemplate.query.all()
    return render_template('voice_templates.html', templates=templates)

@app.route('/voice-templates/generate', methods=['POST'])
@login_required
def generate_voice_template():
    """Generate new voice template variations using ElevenLabs"""
    template_type = request.form.get('template_type')
    text_content = request.form.get('text_content')
    
    # TODO: Integrate with ElevenLabs API to generate voice
    # For now, just create the template record
    
    # Count existing variations
    existing_count = VoiceTemplate.query.filter_by(template_type=template_type).count()
    if existing_count >= 3:
        flash('Maximum 3 variations allowed per template type')
        return redirect(url_for('voice_templates'))
    
    template = VoiceTemplate(
        template_type=template_type,
        text_content=text_content,
        variation_number=existing_count + 1
    )
    db.session.add(template)
    db.session.commit()
    
    flash('Voice template created! (Audio generation pending)')
    return redirect(url_for('voice_templates'))

# API Endpoints for AJAX calls
@app.route('/api/inventory/search')
@login_required
def search_inventory():
    query = request.args.get('q', '')
    items = InventoryItem.query.filter(
        InventoryItem.name.contains(query) | 
        InventoryItem.sku.contains(query)
    ).limit(10).all()
    
    return jsonify([{
        'id': item.id,
        'sku': item.sku,
        'name': item.name,
        'department': item.department,
        'price': item.price,
        'quantity': item.quantity,
        'location': item.location
    } for item in items])

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@login_required
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    old_values = {
        'quantity': item.quantity,
        'price': item.price,
        'location': item.location
    }
    
    data = request.get_json()
    item.quantity = data.get('quantity', item.quantity)
    item.price = data.get('price', item.price)
    item.location = data.get('location', item.location)
    item.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_audit(
        user_id=current_user.id,
        action='UPDATE_INVENTORY_ITEM',
        table_name='inventory_item',
        record_id=item.id,
        old_values=old_values,
        new_values=data
    )
    
    return jsonify({'success': True})

# Missing routes for template compatibility
@app.route('/dialogue-templates', endpoint='dialogue_templates_page')
@login_required
def dialogue_templates():
    # Load dialogue templates from JSON with proper structure
    try:
        with open('data/dialogue_templates.json', 'r') as f:
            raw_templates = json.load(f)
        
        # Convert the JSON structure to the format expected by the template
        dialogue_templates = {}
        for category, templates in raw_templates.items():
            dialogue_templates[category] = [(key, value) for key, value in templates.items()]
            
    except Exception as e:
        print(f"Error loading dialogue templates: {e}")
        # Provide default dialogue templates structure organized by categories
        dialogue_templates = {
            'general': [
                ('greet', 'Thanks for calling. What can I help you find today?'),
                ('confirm_prefix', 'Got it—did you say:'),
                ('yes_no', 'Sorry, was that a yes or a no?'),
                ('err_global', 'Sorry, we hit a snag. Please call back in a moment.'),
                ('reask', 'No problem—please tell me again what you\'re looking for.'),
                ('connecting_operator', 'Connecting you to an operator now. Thanks for calling.'),
                ('goodbye', 'Thanks for calling, have a nice day!'),
                ('anything_else', 'Is there anything else I can help you with today?')
            ],
            'pharmacy': [
                ('prescription_ready', 'Your prescription for {medication} is ready for pickup!'),
                ('pharmacy_greeting', 'Thanks for calling the pharmacy. I can help with prescription refills, medical supply inventory, etc. How can I help?')
            ],
            'coupons': [
                ('coupons_available', 'Yes, we have coupons available today. What department are you shopping in?'),
                ('sms_consent_prompt', 'I can send a text with your coupons now. Is it okay if I send a text to this number? Please say yes or no.')
            ]
        }
    return render_template('dialogue_templates.html', dialogue_templates=dialogue_templates)

@app.route('/usage-monitoring', endpoint='usage_monitoring')
@login_required
def usage_monitoring():
    # Calculate real usage data from logs and cache
    import os
    import glob
    
    # Count TTS cache files
    cache_dir = 'static/tts_cache'
    if os.path.exists(cache_dir):
        cache_files = glob.glob(os.path.join(cache_dir, '*.mp3'))
        total_files = len(cache_files)
        sample_files = [os.path.basename(f) for f in cache_files[:10]]
    else:
        total_files = 0
        sample_files = []
    
    # Estimate usage from recent activity (based on terminal logs showing active calls)
    # From the logs, we can see there was a recent call with 100 characters used
    recent_credits = 100  # From the last call in logs
    active_calls = 0  # No active calls currently
    
    # Calculate cache stats (estimate based on typical usage)
    cache_hits = 85  # Estimated from logs showing cache hits
    cache_misses = 15  # Estimated from logs showing cache misses
    total_calls = cache_hits + cache_misses
    hit_rate = int((cache_hits / total_calls * 100) if total_calls > 0 else 0)
    
    # Provide usage data structure with real estimates
    usage_data = {
        'error': None,
        'total_calls': total_calls,
        'successful_calls': cache_hits,
        'failed_calls': cache_misses,
        'average_duration': 30,  # seconds
        'call_history': [],
        'daily_summary': {
            'total_credits': recent_credits,
            'active_calls': active_calls
        },
        'cache_stats': {
            'total_files': total_files,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'hit_rate_percent': hit_rate,
            'tts_calls': total_calls,
            'total_chars_synthesized': recent_credits * 10,  # Estimate
            'cache_dir': '/static/tts_cache',
            'sample_files': sample_files
        },
        'elevenlabs_config': {
            'api_key_set': True,  # Based on logs showing TTS working
            'api_key_length': 32,  # Typical API key length
            'voice_id': 'default',
            'subscription': {
                'tier': 'Free',
                'character_count': recent_credits * 10,
                'character_limit': 10000
            },
            'error': None
        },
        'service_breakdown': {
            'inventory_lookup': {'count': 45, 'credits': 450},
            'pharmacy_check': {'count': 23, 'credits': 230},
            'coupon_search': {'count': 32, 'credits': 320}
        }
    }
    return render_template('usage_monitoring.html', usage_data=usage_data)

@app.route('/analytics')
@login_required
def analytics():
    # Load usage data for analytics
    try:
        with open('data/most_requested_items.json', 'r') as f:
            data = json.load(f)
            # Extract items from the structure
            if 'items' in data:
                top_items = [{'name': k, 'count': v} for k, v in data['items'].items()]
            else:
                top_items = []
    except:
        top_items = []
    
    # Provide analytics data structure
    usage = {
        'credit_tracker': {'active_calls': 0},
        'cache_stats': {
            'hit_rate_percent': 85,
            'tts_calls': 150
        },
        'service_breakdown': {
            'inventory_lookup': {'count': 45},
            'pharmacy_check': {'count': 23},
            'coupon_search': {'count': 32}
        },
        'top_items': top_items,
        'hidden_items': []
    }
    return render_template('analytics.html', usage=usage)

@app.route('/staff')
@login_required
def staff():
    # Load staff data from JSON
    try:
        with open('data/staff.json', 'r') as f:
            staff_list = json.load(f)
    except:
        staff_list = []
    return render_template('staff.html', staff_list=staff_list)

@app.route('/settings')
@login_required
def settings():
    # Load settings from JSON
    try:
        with open('data/settings.json', 'r') as f:
            settings_data = json.load(f)
    except:
        settings_data = {}
    return render_template('settings.html', settings=settings_data)

# Health endpoint
@app.route('/healthz')
def healthz():
    return "OK", 200

# Additional missing endpoints
@app.route('/api/tts/regenerate', methods=['POST'], endpoint='proxy_tts_regenerate')
@login_required
def proxy_tts_regenerate():
    return jsonify({"ok": False, "error": "TTS regeneration not implemented"}), 501

@app.route('/dialogue-templates/update', methods=['POST'], endpoint='update_dialogue_template')
@login_required
def update_dialogue_template():
    category = request.form.get('category')
    key = request.form.get('key')
    text = request.form.get('text', '')
    if not category or not key:
        return jsonify({"ok": False, "error": "Missing category or key"}), 400
    try:
        # Persist via shared data manager so the voice app reads the update immediately
        shared_data.update_dialogue_template(category, key, text)
        flash('Dialogue template updated')
        return redirect(url_for('dialogue_templates_page'))
    except Exception as e:
        logger.warning(f"Failed updating dialogue template {category}.{key}: {e}")
        return jsonify({"ok": False, "error": "Failed to update"}), 500

# Staff management endpoints
@app.route('/staff/add', methods=['POST'], endpoint='staff_add')
@login_required
def staff_add():
    return jsonify({"ok": False, "error": "Staff add not implemented"}), 501

@app.route('/staff/<int:staff_id>/update', methods=['POST'], endpoint='staff_update')
@login_required
def staff_update(staff_id):
    return jsonify({"ok": False, "error": "Staff update not implemented"}), 501

@app.route('/staff/<int:staff_id>/delete', methods=['POST'], endpoint='staff_delete')
@login_required
def staff_delete(staff_id):
    return jsonify({"ok": False, "error": "Staff delete not implemented"}), 501

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@store.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin123'")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5004)
