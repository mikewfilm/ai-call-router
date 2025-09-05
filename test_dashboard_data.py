#!/usr/bin/env python3
"""
Script to test dashboard data and show what's available
"""

import requests
import json

def test_dashboard_data():
    """Test dashboard data and show what's available"""
    
    base_url = "http://localhost:5004"
    
    print("🔍 Testing Dashboard Data...")
    print("=" * 50)
    
    try:
        # Test login page
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page error: {response.status_code}")
            return
        
        # Test dashboard (should redirect to login)
        response = requests.get(f"{base_url}/")
        if response.status_code == 302:  # Redirect to login
            print("✅ Dashboard redirects to login (as expected)")
        else:
            print(f"⚠️  Dashboard response: {response.status_code}")
        
        print(f"\n🌐 Dashboard URL: {base_url}")
        print(f"🔑 Login URL: {base_url}/login")
        
        print(f"\n📋 Available Pages (after login):")
        print(f"   - Dashboard: {base_url}/")
        print(f"   - Store Info: {base_url}/store-info")
        print(f"   - Departments: {base_url}/departments")
        print(f"   - Inventory: {base_url}/inventory")
        print(f"   - Coupons: {base_url}/coupons")
        print(f"   - Voice Templates: {base_url}/voice-templates")
        print(f"   - Analytics: {base_url}/analytics")
        print(f"   - Staff: {base_url}/staff")
        print(f"   - Settings: {base_url}/settings")
        
        print(f"\n👤 Default Login Credentials:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Open {base_url}/login in your browser")
        print(f"   2. Login with admin/admin123")
        print(f"   3. Check Store Info page to see migrated data")
        print(f"   4. Make changes and test voice app integration")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to dashboard. Is it running?")
        print("   Try: python dashboard_simple.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dashboard_data()
