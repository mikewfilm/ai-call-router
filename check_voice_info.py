#!/usr/bin/env python3
"""
Script to check ElevenLabs voice information
"""

import os
import requests
import re

def load_env_file():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            content = f.read()
            # Handle multi-line values
            lines = content.split('\n')
            current_key = None
            current_value = []
            
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    if current_key:
                        env_vars[current_key] = ''.join(current_value).strip()
                        current_value = []
                    
                    key, value = line.split('=', 1)
                    current_key = key.strip()
                    current_value.append(value.strip())
                elif current_key and line.strip():
                    current_value.append(line.strip())
            
            if current_key:
                env_vars[current_key] = ''.join(current_value).strip()
                
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return {}
    
    return env_vars

def check_voice_info():
    """Check the current ElevenLabs voice information"""
    
    env_vars = load_env_file()
    voice_id = env_vars.get("ELEVENLABS_VOICE_ID")
    api_key = env_vars.get("ELEVENLABS_API_KEY")
    
    if not voice_id:
        print("❌ ELEVENLABS_VOICE_ID not found in .env file")
        return
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in .env file")
        return
    
    print(f"🎤 Checking voice information...")
    print(f"Voice ID: {voice_id}")
    
    try:
        # Get voice details from ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
        headers = {
            "xi-api-key": api_key
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            voice_data = response.json()
            print(f"✅ Voice Name: {voice_data.get('name', 'Unknown')}")
            print(f"✅ Voice Description: {voice_data.get('description', 'No description')}")
            print(f"✅ Voice Category: {voice_data.get('category', 'Unknown')}")
            print(f"✅ Voice Labels: {voice_data.get('labels', {})}")
            
            # Check if it's Burt Reynolds
            voice_name = voice_data.get('name', '').lower()
            if 'burt' in voice_name or 'reynolds' in voice_name:
                print("🎯 This appears to be the Burt Reynolds voice!")
            else:
                print("ℹ️  This is not the Burt Reynolds voice")
                
        else:
            print(f"❌ Failed to get voice info: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking voice info: {e}")

if __name__ == "__main__":
    check_voice_info()
