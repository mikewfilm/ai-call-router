import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

class SharedDataManager:
    """Manages shared data between the dashboard and voice app"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.lock = threading.Lock()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize data files
        self.files = {
            'store_info': os.path.join(data_dir, 'store_info.json'),
            'departments': os.path.join(data_dir, 'departments.json'),
            'inventory': os.path.join(data_dir, 'inventory.json'),
            'coupons': os.path.join(data_dir, 'coupons.json'),
            'voice_templates': os.path.join(data_dir, 'voice_templates.json'),
            'dialogue_templates': os.path.join(data_dir, 'dialogue_templates.json'),
            'staff': os.path.join(data_dir, 'staff.json'),
            'settings': os.path.join(data_dir, 'settings.json')
        }
        
        # Initialize default data if files don't exist
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default data if files don't exist"""
        
        # Default store info - using actual current voice app data
        if not os.path.exists(self.files['store_info']):
            # Get current store info from environment variables or use defaults
            store_name = os.getenv("STORE_NAME", "the store")
            store_hours = os.getenv("STORE_HOURS", "Mon–Sat 9am–9pm, Sun 10am–6pm")
            store_address = os.getenv("STORE_ADDRESS", "123 Main St")
            store_city = os.getenv("STORE_CITY", "")
            store_state = os.getenv("STORE_STATE", "")
            store_zip = os.getenv("STORE_ZIP", "")
            store_phone = os.getenv("STORE_PHONE", "(555) 123-4567")
            
            # Build full address
            full_address = store_address
            if store_city:
                full_address += f", {store_city}"
            if store_state:
                full_address += f", {store_state}"
            if store_zip:
                full_address += f" {store_zip}"
            
            default_store_info = {
                'name': store_name.title() if store_name != "the store" else "Your Store",
                'address': full_address,
                'phone': store_phone,
                'hours': store_hours,
                'holiday_hours': os.getenv("HOLIDAYS_SPECIAL_HOURS", "Open most holidays with regular hours; closed on Christmas Day, Thanksgiving Day, New Year's Day, Easter Sunday."),
                'greeting_message': 'Thank you for calling our store. How can I help you today?',
                'hold_message': 'Please hold while I connect you to the appropriate department.',
                'updated_at': datetime.now().isoformat()
            }
            self._save_data('store_info', default_store_info)
        
        # Default departments - using actual current voice app departments
        if not os.path.exists(self.files['departments']):
            default_departments = [
                {
                    'id': 1,
                    'name': 'Grocery',
                    'phone_extension': '101',
                    'description': 'Food items and groceries',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'name': 'Meat & Seafood',
                    'phone_extension': '102',
                    'description': 'Fresh meat and seafood',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 3,
                    'name': 'Deli',
                    'phone_extension': '103',
                    'description': 'Deli meats, cheeses, and prepared foods',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 4,
                    'name': 'Bakery',
                    'phone_extension': '104',
                    'description': 'Fresh baked goods and breads',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 5,
                    'name': 'Electronics',
                    'phone_extension': '105',
                    'description': 'Electronics and gadgets',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 6,
                    'name': 'Home and Garden',
                    'phone_extension': '106',
                    'description': 'Home improvement and garden supplies',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 7,
                    'name': 'Health and Beauty',
                    'phone_extension': '107',
                    'description': 'Personal care and beauty products',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 8,
                    'name': 'Pet Supplies',
                    'phone_extension': '108',
                    'description': 'Pet food, toys, and supplies',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 9,
                    'name': 'Customer Service',
                    'phone_extension': '109',
                    'description': 'General customer service and inquiries',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
            ]
            self._save_data('departments', default_departments)
        
        # Default inventory
        if not os.path.exists(self.files['inventory']):
            default_inventory = [
                {
                    'id': 1,
                    'name': 'Milk (Gallon)',
                    'sku': 'MLK001',
                    'department': 'Grocery',
                    'price': 3.99,
                    'stock_quantity': 50,
                    'location': 'Aisle 1',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'name': 'Bread (Whole Wheat)',
                    'sku': 'BRD001',
                    'department': 'Bakery',
                    'price': 2.49,
                    'stock_quantity': 25,
                    'location': 'Bakery Section',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 3,
                    'name': 'Purina Cat Food',
                    'sku': 'PET001',
                    'department': 'Pet Supplies',
                    'price': 12.99,
                    'stock_quantity': 30,
                    'location': 'Pet Supplies Aisle',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
            ]
            self._save_data('inventory', default_inventory)
        
        # Default coupons
        if not os.path.exists(self.files['coupons']):
            default_coupons = [
                {
                    'id': 1,
                    'code': 'SAVE20',
                    'description': '20% off all groceries',
                    'discount_type': 'percentage',
                    'discount_value': 20,
                    'is_store_wide': True,
                    'is_active': True,
                    'expires_at': '2024-12-31T23:59:59',
                    'created_at': datetime.now().isoformat()
                }
            ]
            self._save_data('coupons', default_coupons)
        
        # Default voice templates
        if not os.path.exists(self.files['voice_templates']):
            default_templates = [
                {
                    'id': 1,
                    'template_type': 'greeting',
                    'text_content': 'Thank you for calling our store. How can I help you today?',
                    'is_active': True,
                    'variation_number': 1,
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'template_type': 'hold',
                    'text_content': 'Please hold while I connect you to the appropriate department.',
                    'is_active': True,
                    'variation_number': 1,
                    'created_at': datetime.now().isoformat()
                }
            ]
            self._save_data('voice_templates', default_templates)
        
        # Default dialogue templates
        if not os.path.exists(self.files['dialogue_templates']):
            default_dialogue_templates = {
                "general": {
                    "greet": "Thanks for calling. What can I help you find today?",
                    "confirm_prefix": "Got it—did you say:",
                    "yes_no": "Sorry, was that a yes or a no?",
                    "err_global": "Sorry, we hit a snag. Please call back in a moment.",
                    "err_confirm": "Sorry, we had trouble processing that. Goodbye.",
                    "no_record": "Sorry, we did not get your message. Goodbye.",
                    "reask": "No problem—please tell me again what you're looking for.",
                    "reask_cap": "No worries—tell me again what you need so I get it right.",
                    "connecting_operator": "Connecting you to an operator now. Thanks for calling.",
                    "timeout": "I've been helping you for a while now. Thank you for calling, and have a nice day!",
                    "thanks_calling": "Thanks for calling!",
                    "goodbye": "Thanks for calling, have a nice day!",
                    "error_goodbye": "Sorry, there was an error. Goodbye.",
                    "error_processing": "Sorry, there was an error processing your request. Please try again.",
                    "no_speech": "I didn't hear a response. Please call back and try again. Goodbye.",
                    "hit_snag": "Sorry, we hit a snag.",
                    "anything_else": "Is there anything else I can help you with today?"
                },
                "pharmacy": {
                    "pharmacy_greeting": "You're through to the pharmacy. I can help with prescription refills, checking if a prescription is ready, transfers, pharmacist questions, pharmacy hours and location, or medical supplies. Which would you like? You can say, for example, 'refill same as last time' or give your RX or phone number.",
                    "prescription_ready": "Your prescription for {medication} is ready for pickup!",
                    "prescription_processing": "Your prescription for {medication} is being processed and should be ready in about 15-20 minutes.",
                    "prescription_delayed": "Your prescription for {medication} has been delayed. We're waiting for additional information from your doctor.",
                    "prescription_out_of_stock": "Your prescription for {medication} is out of stock. We've ordered more and expect it in 2-3 business days.",
                    "no_prescriptions_found": "I couldn't find any prescriptions with that phone number. Please check the number or provide your RX number. Would you like me to connect you to our pharmacy staff to help?",
                    "no_rx_found": "I couldn't find a prescription with that RX number. Please check the number and try again. Would you like me to connect you to our pharmacy staff to help?",
                    "transfer_from_pharmacy": "I can help you transfer your prescription from {pharmacy}. I'll need your RX number and the name of the medication. Let me connect you to our pharmacy staff to complete the transfer.",
                    "transfer_general": "I can help you transfer your prescription. I'll need to know which pharmacy you're transferring from and your RX number. Let me connect you to our pharmacy staff.",
                    "status_check_prompt": "I'd be happy to check your prescription status. Could you please provide your RX number or phone number?",
                    "refill_prompt": "I found your prescriptions, but none are currently being processed. Would you like to request a refill?"
                },
                "coupons": {
                    "coupons_available": "Yes, we have coupons available today. What department are you shopping in?",
                    "no_coupons_for_item": "I don't see any current coupons available for {item}. However, we do have some general store coupons that might help you save on your overall purchase.",
                    "no_specific_coupons": "I don't see any specific coupons for that item, but we do have several store-wide promotions available.",
                    "department_coupons_intro": "Here are the current {department} coupons available. ",
                    "no_department_coupons": "I don't see any specific {department} coupons for {item} right now, but you can check our weekly ad for current specials.",
                    "help_find_coupons": "I can help you find {department} coupons. Please check our weekly ad or ask a store associate for current specials.",
                    "coupon_replay_prompt": "To hear these coupons again, say repeat or press any key.",
                    "coupon_replay_thanks": "Thanks for calling!",
                    "sms_consent_prompt": "I can send a text with your coupons now. Is it okay if I send a text to this number? Please say yes or no.",
                    "sms_body": "Thanks! Here are today's coupons: …",
                    "sms_consent_thanks_yes": "Thanks—I'll send that text now.",
                    "sms_consent_thanks_no": "No problem, I won't send a text."
                },
                "spanish": {
                    "greet": "Gracias por llamar. ¿Qué puedo ayudarle a encontrar hoy?",
                    "confirm_prefix": "Entendido—¿dijo:",
                    "yes_no": "Perdón, ¿fue un sí o un no?",
                    "err_global": "Lo sentimos, hubo un problema. Por favor, vuelva a llamar en un momento.",
                    "err_confirm": "Lo sentimos, hubo un problema con su respuesta. Adiós.",
                    "no_record": "Lo sentimos, no recibimos su mensaje. Adiós.",
                    "reask": "No hay problema—dígame otra vez qué está buscando.",
                    "reask_cap": "Sin problema—repítame lo que necesita para acertar.",
                    "connecting_operator": "Le conecto con un operador ahora. Gracias por llamar."
                }
            }
            self._save_data('dialogue_templates', default_dialogue_templates)
        
        # Default staff
        if not os.path.exists(self.files['staff']):
            default_staff = [
                {
                    'id': 1,
                    'name': 'John Smith',
                    'email': 'john.smith@store.com',
                    'phone': '(555) 123-4567',
                    'department': 'Customer Service',
                    'role': 'Manager',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
            ]
            self._save_data('staff', default_staff)
        
        # Default settings
        if not os.path.exists(self.files['settings']):
            default_settings = {
                'ai_model': 'gpt-4',
                'voice_settings': {
                    'voice_id': 'default',
                    'stability': 0.5,
                    'similarity_boost': 0.75
                },
                'system_preferences': {
                    'timeout_seconds': 30,
                    'max_retries': 3,
                    'enable_analytics': True
                },
                'updated_at': datetime.now().isoformat()
            }
            self._save_data('settings', default_settings)
    
    def _load_data(self, data_type: str) -> Any:
        """Load data from JSON file"""
        try:
            with open(self.files[data_type], 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] if data_type in ['departments', 'inventory', 'coupons', 'voice_templates', 'staff'] else {}
    
    def _save_data(self, data_type: str, data: Any) -> None:
        """Save data to JSON file"""
        with self.lock:
            with open(self.files[data_type], 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    # Store Info Methods
    def get_store_info(self) -> Dict[str, Any]:
        """Get store information"""
        return self._load_data('store_info')
    
    def update_store_info(self, store_info: Dict[str, Any]) -> None:
        """Update store information"""
        store_info['updated_at'] = datetime.now().isoformat()
        self._save_data('store_info', store_info)
    
    # Department Methods
    def get_departments(self) -> List[Dict[str, Any]]:
        """Get all departments"""
        return self._load_data('departments')
    
    def get_department_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get department by name"""
        departments = self.get_departments()
        for dept in departments:
            if dept['name'].lower() == name.lower():
                return dept
        return None
    
    def add_department(self, department: Dict[str, Any]) -> None:
        """Add a new department"""
        departments = self.get_departments()
        department['id'] = max([d['id'] for d in departments], default=0) + 1
        department['created_at'] = datetime.now().isoformat()
        departments.append(department)
        self._save_data('departments', departments)
    
    def update_department(self, dept_id: int, department: Dict[str, Any]) -> bool:
        """Update a department"""
        departments = self.get_departments()
        for i, dept in enumerate(departments):
            if dept['id'] == dept_id:
                department['id'] = dept_id
                department['created_at'] = dept['created_at']
                departments[i] = department
                self._save_data('departments', departments)
                return True
        return False
    
    # Inventory Methods
    def get_inventory(self) -> List[Dict[str, Any]]:
        """Get all inventory items"""
        return self._load_data('inventory')
    
    def get_inventory_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by name"""
        inventory = self.get_inventory()
        for item in inventory:
            if name.lower() in item['name'].lower():
                return item
        return None
    
    def add_inventory_item(self, item: Dict[str, Any]) -> None:
        """Add a new inventory item"""
        inventory = self.get_inventory()
        item['id'] = max([i['id'] for i in inventory], default=0) + 1
        item['created_at'] = datetime.now().isoformat()
        inventory.append(item)
        self._save_data('inventory', inventory)
    
    def update_inventory_item(self, item_id: int, item: Dict[str, Any]) -> bool:
        """Update an inventory item"""
        inventory = self.get_inventory()
        for i, inv_item in enumerate(inventory):
            if inv_item['id'] == item_id:
                item['id'] = item_id
                item['created_at'] = inv_item['created_at']
                inventory[i] = item
                self._save_data('inventory', inventory)
                return True
        return False
    
    # Coupon Methods
    def get_coupons(self) -> List[Dict[str, Any]]:
        """Get all coupons"""
        return self._load_data('coupons')
    
    def add_coupon(self, coupon: Dict[str, Any]) -> None:
        """Add a new coupon"""
        coupons = self.get_coupons()
        coupon['id'] = max([c['id'] for c in coupons], default=0) + 1
        coupon['created_at'] = datetime.now().isoformat()
        coupons.append(coupon)
        self._save_data('coupons', coupons)
    
    # Voice Template Methods
    def get_voice_templates(self) -> List[Dict[str, Any]]:
        """Get all voice templates"""
        return self._load_data('voice_templates')
    
    def get_voice_template_by_type(self, template_type: str) -> Optional[Dict[str, Any]]:
        """Get voice template by type"""
        templates = self.get_voice_templates()
        for template in templates:
            if template['template_type'] == template_type and template['is_active']:
                return template
        return None
    
    def add_voice_template(self, template: Dict[str, Any]) -> None:
        """Add a new voice template"""
        templates = self.get_voice_templates()
        template['id'] = max([t['id'] for t in templates], default=0) + 1
        template['created_at'] = datetime.now().isoformat()
        templates.append(template)
        self._save_data('voice_templates', templates)
    
    # Dialogue Template Methods
    def get_dialogue_templates(self) -> Dict[str, Any]:
        """Get all dialogue templates"""
        templates = self._load_data('dialogue_templates')
        # Ensure critical keys exist (non-destructive merge)
        changed = False
        # Pharmacy greeting prompt used by voice app
        pharm_defaults = {
            "pharmacy_greeting": "You're through to the pharmacy. I can help with prescription refills, checking if a prescription is ready, transfers, pharmacist questions, pharmacy hours and location, or medical supplies. Which would you like? You can say, for example, 'refill same as last time' or give your RX or phone number."
        }
        if 'pharmacy' not in templates:
            templates['pharmacy'] = {}
            changed = True
        for k, v in pharm_defaults.items():
            if k not in templates['pharmacy']:
                templates['pharmacy'][k] = v
                changed = True
        if changed:
            self._save_data('dialogue_templates', templates)
        return templates
    
    def get_dialogue_template(self, category: str, key: str) -> Optional[str]:
        """Get a specific dialogue template"""
        templates = self.get_dialogue_templates()
        return templates.get(category, {}).get(key)
    
    def update_dialogue_template(self, category: str, key: str, text: str) -> None:
        """Update a specific dialogue template"""
        templates = self.get_dialogue_templates()
        if category not in templates:
            templates[category] = {}
        templates[category][key] = text
        self._save_data('dialogue_templates', templates)
    
    def update_dialogue_category(self, category: str, templates: Dict[str, str]) -> None:
        """Update all templates in a category"""
        all_templates = self.get_dialogue_templates()
        all_templates[category] = templates
        self._save_data('dialogue_templates', all_templates)
    
    # Staff Methods
    def get_staff(self) -> List[Dict[str, Any]]:
        """Get all staff members"""
        return self._load_data('staff')

    def add_staff(self, staff: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new staff member and return it."""
        staff_list = self.get_staff()
        new_id = max([s.get('id', 0) for s in staff_list], default=0) + 1
        staff['id'] = new_id
        staff['created_at'] = datetime.now().isoformat()
        if 'is_active' not in staff:
            staff['is_active'] = True
        staff_list.append(staff)
        self._save_data('staff', staff_list)
        return staff

    def update_staff(self, staff_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing staff member by id."""
        staff_list = self.get_staff()
        for i, s in enumerate(staff_list):
            if int(s.get('id', 0)) == int(staff_id):
                updated = dict(s)
                updated.update({k: v for k, v in updates.items() if v is not None})
                updated['id'] = s['id']
                updated['created_at'] = s.get('created_at')
                staff_list[i] = updated
                self._save_data('staff', staff_list)
                return True
        return False

    def delete_staff(self, staff_id: int) -> bool:
        """Delete a staff member by id."""
        staff_list = self.get_staff()
        new_list = [s for s in staff_list if int(s.get('id', 0)) != int(staff_id)]
        if len(new_list) != len(staff_list):
            self._save_data('staff', new_list)
            return True
        return False
    
    # Settings Methods
    def get_settings(self) -> Dict[str, Any]:
        """Get system settings"""
        return self._load_data('settings')
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update system settings"""
        settings['updated_at'] = datetime.now().isoformat()
        self._save_data('settings', settings)

# Global instance
shared_data = SharedDataManager()
