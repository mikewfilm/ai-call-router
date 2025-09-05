#!/usr/bin/env python3
"""
Script to migrate existing voice app data to populate the dashboard
"""

import os
import json
from datetime import datetime
from shared_data_manager import shared_data

def migrate_voice_app_data():
    """Migrate current voice app data to shared data system"""
    
    print("🔄 Migrating Voice App Data to Dashboard...")
    print("=" * 50)
    
    # Get current voice app store info from environment variables
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
    
    # Update store info with current voice app data
    current_store_info = {
        'name': store_name.title() if store_name != "the store" else "Your Store",
        'address': full_address,
        'phone': store_phone,
        'hours': store_hours,
        'greeting_message': 'Thank you for calling our store. How can I help you today?',
        'hold_message': 'Please hold while I connect you to the appropriate department.',
        'updated_at': datetime.now().isoformat()
    }
    
    shared_data.update_store_info(current_store_info)
    print(f"✅ Store Info Updated:")
    print(f"   Name: {current_store_info['name']}")
    print(f"   Address: {current_store_info['address']}")
    print(f"   Phone: {current_store_info['phone']}")
    print(f"   Hours: {current_store_info['hours']}")
    
    # Check if we need to update departments
    current_departments = shared_data.get_departments()
    if not current_departments:
        print("\n📋 No departments found, creating default departments...")
        # This will be handled by the shared data manager initialization
    else:
        print(f"\n📋 Found {len(current_departments)} departments")
        for dept in current_departments:
            print(f"   - {dept['name']} (ext: {dept['phone_extension']})")
    
    # Check if we need to update inventory
    current_inventory = shared_data.get_inventory()
    if not current_inventory:
        print("\n📦 No inventory found, creating sample inventory...")
        # This will be handled by the shared data manager initialization
    else:
        print(f"\n📦 Found {len(current_inventory)} inventory items")
        for item in current_inventory[:5]:  # Show first 5
            print(f"   - {item['name']} (${item['price']})")
    
    # Check if we need to update coupons
    current_coupons = shared_data.get_coupons()
    if not current_coupons:
        print("\n🎫 No coupons found, creating sample coupons...")
        # This will be handled by the shared data manager initialization
    else:
        print(f"\n🎫 Found {len(current_coupons)} coupons")
        for coupon in current_coupons:
            print(f"   - {coupon['code']}: {coupon['description']}")
    
    # Check if we need to update voice templates
    current_templates = shared_data.get_voice_templates()
    if not current_templates:
        print("\n🎤 No voice templates found, creating default templates...")
        # This will be handled by the shared data manager initialization
    else:
        print(f"\n🎤 Found {len(current_templates)} voice templates")
        for template in current_templates:
            print(f"   - {template['template_type']}: {template['text_content'][:50]}...")
    
    print("\n" + "=" * 50)
    print("✅ Migration Complete!")
    print("\n📋 Next Steps:")
    print("1. Restart the dashboard: ./start_dashboard_simple.sh")
    print("2. Check that the data appears correctly")
    print("3. Make any additional updates as needed")
    
    return True

def show_current_data():
    """Show current data in the shared system"""
    
    print("📊 Current Data in Shared System:")
    print("=" * 50)
    
    # Store Info
    store_info = shared_data.get_store_info()
    print(f"\n🏪 Store Info:")
    print(f"   Name: {store_info.get('name', 'Not set')}")
    print(f"   Address: {store_info.get('address', 'Not set')}")
    print(f"   Phone: {store_info.get('phone', 'Not set')}")
    print(f"   Hours: {store_info.get('hours', 'Not set')}")
    print(f"   Greeting: {store_info.get('greeting_message', 'Not set')}")
    
    # Departments
    departments = shared_data.get_departments()
    print(f"\n📋 Departments ({len(departments)}):")
    for dept in departments:
        print(f"   - {dept['name']} (ext: {dept['phone_extension']})")
    
    # Inventory
    inventory = shared_data.get_inventory()
    print(f"\n📦 Inventory ({len(inventory)}):")
    for item in inventory:
        print(f"   - {item['name']} (${item['price']}) - {item['department']}")
    
    # Coupons
    coupons = shared_data.get_coupons()
    print(f"\n🎫 Coupons ({len(coupons)}):")
    for coupon in coupons:
        print(f"   - {coupon['code']}: {coupon['description']}")
    
    # Voice Templates
    templates = shared_data.get_voice_templates()
    print(f"\n🎤 Voice Templates ({len(templates)}):")
    for template in templates:
        print(f"   - {template['template_type']}: {template['text_content'][:50]}...")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_current_data()
    else:
        migrate_voice_app_data()

if __name__ == "__main__":
    main()
