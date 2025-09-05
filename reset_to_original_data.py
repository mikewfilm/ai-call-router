#!/usr/bin/env python3
"""
Script to reset shared data to match original voice app configuration
"""

from shared_data_manager import shared_data
from datetime import datetime

def reset_to_original_data():
    """Reset shared data to original voice app configuration"""
    
    print("🔄 Resetting to Original Voice App Data...")
    print("=" * 50)
    
    # Original voice app configuration
    original_store_info = {
        'name': 'Your Store',  # "the store" becomes "Your Store" for display
        'address': '123 Main St',
        'phone': '(555) 123-4567',
        'hours': 'Mon–Sat 9am–9pm, Sun 10am–6pm',
        'greeting_message': 'Thank you for calling our store. How can I help you today?',
        'hold_message': 'Please hold while I connect you to the appropriate department.',
        'updated_at': datetime.now().isoformat()
    }
    
    # Update the shared data
    shared_data.update_store_info(original_store_info)
    
    print("✅ Store Info Reset:")
    print(f"   Name: {original_store_info['name']}")
    print(f"   Address: {original_store_info['address']}")
    print(f"   Phone: {original_store_info['phone']}")
    print(f"   Hours: {original_store_info['hours']}")
    print(f"   Greeting: {original_store_info['greeting_message']}")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Refresh the dashboard at http://localhost:5004/store-info")
    print(f"2. You should now see the original voice app data")
    print(f"3. Test the voice app to confirm it matches")
    print(f"4. Make changes in the dashboard to test integration")

if __name__ == "__main__":
    reset_to_original_data()
