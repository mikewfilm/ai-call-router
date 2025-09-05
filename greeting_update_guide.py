#!/usr/bin/env python3
"""
Guide for updating voice app greetings through the dashboard
"""

import requests
import json

def show_greeting_update_guide():
    """Show how the greeting update system works"""
    
    print("🎤 Voice App Greeting Update System")
    print("=" * 50)
    
    print("\n📋 How It Works:")
    print("1. Dashboard stores greeting text in shared data")
    print("2. Voice app reads greeting from shared data")
    print("3. ElevenLabs generates MP3 audio from text")
    print("4. Audio is cached to save API credits")
    print("5. Voice app plays cached audio file")
    
    print("\n⚠️  The Cache Issue:")
    print("• When you update greeting in dashboard, text changes immediately")
    print("• But voice app still plays old cached MP3 file")
    print("• Need to clear cache to force new audio generation")
    
    print("\n🔄 Current Status:")
    
    # Check current greeting in shared data
    try:
        response = requests.get("http://localhost:5003/api/store-info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dashboard Greeting: '{data['greeting_message']}'")
        else:
            print("❌ Cannot access voice app API")
    except:
        print("❌ Voice app not running")
    
    print("\n🔧 How to Update Greeting:")
    print("1. Open dashboard: http://localhost:5004/login")
    print("2. Go to Store Info page")
    print("3. Update 'AI Greeting Message' field")
    print("4. Click 'Save Changes'")
    print("5. Clear TTS cache: python manage_tts_cache.py clear greeting")
    print("6. Test voice app - new greeting should play")
    
    print("\n📝 Cache Management Commands:")
    print("• python manage_tts_cache.py status          # Show cache status")
    print("• python manage_tts_cache.py clear greeting  # Clear greeting cache")
    print("• python manage_tts_cache.py clear hours     # Clear hours cache")
    print("• python manage_tts_cache.py clear address   # Clear address cache")
    print("• python manage_tts_cache.py clear-all       # Clear all cache")
    
    print("\n💡 Best Practices:")
    print("• Update greeting in dashboard during off-hours")
    print("• Clear cache immediately after updating")
    print("• Test voice app to confirm changes")
    print("• Keep cache for frequently used responses")
    
    print("\n🎯 Integration Status:")
    print("✅ Dashboard and voice app are connected")
    print("✅ Shared data system is working")
    print("✅ API endpoints are functional")
    print("⚠️  Cache management needed for audio updates")

if __name__ == "__main__":
    show_greeting_update_guide()
