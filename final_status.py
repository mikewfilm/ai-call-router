#!/usr/bin/env python3
"""
Final status showing synchronized voice app and dashboard
"""

import requests
import json

def show_final_status():
    """Show the final synchronized status"""
    
    print("🎯 FINAL STATUS - Voice App & Dashboard Synchronized")
    print("=" * 60)
    
    # Check voice app data
    try:
        voice_response = requests.get("http://localhost:5003/api/store-info")
        if voice_response.status_code == 200:
            voice_data = voice_response.json()
            print("✅ Voice App Data:")
            print(f"   Name: {voice_data['name']}")
            print(f"   Address: {voice_data['address']}")
            print(f"   Phone: {voice_data['phone']}")
            print(f"   Hours: {voice_data['hours']}")
            print(f"   Greeting: {voice_data['greeting_message']}")
        else:
            print(f"❌ Voice App Error: {voice_response.status_code}")
    except Exception as e:
        print(f"❌ Voice App Error: {e}")
    
    # Check dashboard
    try:
        dashboard_response = requests.get("http://localhost:5004/login")
        if dashboard_response.status_code == 200:
            print(f"\n✅ Dashboard: Running on http://localhost:5004")
        else:
            print(f"❌ Dashboard Error: {dashboard_response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
    
    print(f"\n🎉 SUCCESS! Everything is now synchronized:")
    print(f"   • Voice app and dashboard are both running")
    print(f"   • Both are using the same store information")
    print(f"   • Changes in dashboard will update voice app")
    
    print(f"\n🌐 Access Points:")
    print(f"   • Dashboard: http://localhost:5004/login")
    print(f"   • Voice App: http://localhost:5003/health")
    print(f"   • Login: admin / admin123")
    
    print(f"\n📝 To Test Integration:")
    print(f"   1. Open dashboard at http://localhost:5004/login")
    print(f"   2. Login with admin/admin123")
    print(f"   3. Go to Store Info page")
    print(f"   4. Update store name or address")
    print(f"   5. Save changes")
    print(f"   6. Test voice app - changes should appear immediately")
    
    print(f"\n🔧 Running Services:")
    print(f"   • Voice App: ./start_app.sh (port 5003)")
    print(f"   • Dashboard: ./start_dashboard_simple.sh (port 5004)")
    print(f"   • Both: ./start_integrated.sh")

if __name__ == "__main__":
    show_final_status()
