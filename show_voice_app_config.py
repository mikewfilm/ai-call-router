#!/usr/bin/env python3
"""
Script to show current voice app configuration
"""

import os

def show_voice_app_config():
    """Show current voice app configuration"""
    
    print("🎤 Current Voice App Configuration:")
    print("=" * 50)
    
    # Store configuration
    store_name = os.getenv("STORE_NAME", "the store")
    store_hours = os.getenv("STORE_HOURS", "Mon–Sat 9am–9pm, Sun 10am–6pm")
    store_address = os.getenv("STORE_ADDRESS", "123 Main St")
    store_city = os.getenv("STORE_CITY", "")
    store_state = os.getenv("STORE_STATE", "")
    store_zip = os.getenv("STORE_ZIP", "")
    store_phone = os.getenv("STORE_PHONE", "(555) 123-4567")
    
    print(f"\n🏪 Store Configuration:")
    print(f"   STORE_NAME: {store_name}")
    print(f"   STORE_HOURS: {store_hours}")
    print(f"   STORE_ADDRESS: {store_address}")
    print(f"   STORE_CITY: {store_city or '(not set)'}")
    print(f"   STORE_STATE: {store_state or '(not set)'}")
    print(f"   STORE_ZIP: {store_zip or '(not set)'}")
    print(f"   STORE_PHONE: {store_phone}")
    
    # Build full address
    full_address = store_address
    if store_city:
        full_address += f", {store_city}"
    if store_state:
        full_address += f", {store_state}"
    if store_zip:
        full_address += f" {store_zip}"
    
    print(f"\n📍 Full Address: {full_address}")
    
    # Other configuration
    returns_policy = os.getenv("RETURNS_POLICY", "Most items within 30 days with receipt.")
    holidays_closed = os.getenv("HOLIDAYS_CLOSED", "Christmas Day, Thanksgiving Day, New Year's Day, Easter Sunday")
    holidays_special = os.getenv("HOLIDAYS_SPECIAL_HOURS", "Christmas Eve: 9am-6pm, New Year's Eve: 9am-6pm")
    call_timeout = os.getenv("CALL_TIMEOUT_SECONDS", "120")
    
    print(f"\n⚙️  Other Configuration:")
    print(f"   RETURNS_POLICY: {returns_policy}")
    print(f"   HOLIDAYS_CLOSED: {holidays_closed}")
    print(f"   HOLIDAYS_SPECIAL_HOURS: {holidays_special}")
    print(f"   CALL_TIMEOUT_SECONDS: {call_timeout}")
    
    print(f"\n💡 To customize these values, set environment variables:")
    print(f"   export STORE_NAME='Your Store Name'")
    print(f"   export STORE_ADDRESS='Your Address'")
    print(f"   export STORE_CITY='Your City'")
    print(f"   export STORE_STATE='Your State'")
    print(f"   export STORE_ZIP='Your ZIP'")
    print(f"   export STORE_PHONE='Your Phone'")
    print(f"   export STORE_HOURS='Your Hours'")

if __name__ == "__main__":
    show_voice_app_config()
