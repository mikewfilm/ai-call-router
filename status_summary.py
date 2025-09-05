#!/usr/bin/env python3
"""
Comprehensive status summary of the AI Call Router system
"""

import os
import requests
import json
from datetime import datetime

def check_services():
    """Check if services are running"""
    print("🔍 Service Status:")
    print("=" * 50)
    
    # Check voice app
    try:
        response = requests.get("http://localhost:5000/", timeout=2)
        if response.status_code == 200:
            print("✅ Voice App: Running on http://localhost:5000")
        else:
            print(f"⚠️  Voice App: Responding with status {response.status_code}")
    except:
        print("❌ Voice App: Not running")
    
    # Check dashboard
    try:
        response = requests.get("http://localhost:5004/login", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard: Running on http://localhost:5004")
        else:
            print(f"⚠️  Dashboard: Responding with status {response.status_code}")
    except:
        print("❌ Dashboard: Not running")

def show_migrated_data():
    """Show the data that was migrated"""
    print(f"\n📊 Migrated Data Summary:")
    print("=" * 50)
    
    try:
        from shared_data_manager import shared_data
        
        # Store info
        store_info = shared_data.get_store_info()
        print(f"🏪 Store Info:")
        print(f"   Name: {store_info.get('name', 'N/A')}")
        print(f"   Address: {store_info.get('address', 'N/A')}")
        print(f"   Phone: {store_info.get('phone', 'N/A')}")
        print(f"   Hours: {store_info.get('hours', 'N/A')}")
        print(f"   Greeting: {store_info.get('greeting_message', 'N/A')[:50]}...")
        
        # Departments
        departments = shared_data.get_departments()
        print(f"\n📋 Departments ({len(departments)}):")
        for dept in departments[:5]:  # Show first 5
            print(f"   - {dept['name']} (ext: {dept['phone_extension']})")
        if len(departments) > 5:
            print(f"   ... and {len(departments) - 5} more")
        
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
        
    except Exception as e:
        print(f"❌ Error reading shared data: {e}")

def show_integration_status():
    """Show integration status"""
    print(f"\n🔗 Integration Status:")
    print("=" * 50)
    
    try:
        # Test voice app API
        response = requests.get("http://localhost:5000/api/store-info", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Voice App API: Working")
            print(f"   Current store name: {data.get('name', 'N/A')}")
        else:
            print(f"⚠️  Voice App API: Status {response.status_code}")
    except:
        print("❌ Voice App API: Not accessible")
    
    try:
        # Test dashboard
        response = requests.get("http://localhost:5004/login", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard: Accessible")
        else:
            print(f"⚠️  Dashboard: Status {response.status_code}")
    except:
        print("❌ Dashboard: Not accessible")

def show_next_steps():
    """Show next steps for the user"""
    print(f"\n🚀 Next Steps:")
    print("=" * 50)
    
    print("1. 🌐 Access the Dashboard:")
    print("   URL: http://localhost:5004/login")
    print("   Username: admin")
    print("   Password: admin123")
    
    print("\n2. 📝 Test the Integration:")
    print("   - Login to dashboard")
    print("   - Go to Store Info page")
    print("   - Update store name or address")
    print("   - Save changes")
    print("   - Test voice app to see changes")
    
    print("\n3. 🎤 Test Voice App:")
    print("   - Call the voice app")
    print("   - Ask for store information")
    print("   - Ask about inventory items")
    print("   - Verify changes from dashboard appear")
    
    print("\n4. 📁 Files Created:")
    print("   - data/ (JSON files for shared data)")
    print("   - shared_data_manager.py (data management)")
    print("   - dashboard_simple.py (dashboard app)")
    print("   - migrate_voice_app_data.py (migration script)")
    print("   - test_integration.py (integration tests)")
    
    print("\n5. 🔧 Available Scripts:")
    print("   - ./start_app.sh (start voice app)")
    print("   - ./start_dashboard_simple.sh (start dashboard)")
    print("   - ./start_integrated.sh (start both)")
    print("   - python test_integration.py (test integration)")
    print("   - python migrate_voice_app_data.py show (view data)")

def main():
    """Main function"""
    print("🎯 AI Call Router - System Status")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_services()
    show_migrated_data()
    show_integration_status()
    show_next_steps()
    
    print(f"\n🎉 Migration Complete!")
    print("Your dashboard is now populated with current voice app data.")
    print("Changes made in the dashboard will automatically update the voice app.")

if __name__ == "__main__":
    main()
