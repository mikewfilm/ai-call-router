#!/usr/bin/env python3
"""
Test script to identify response time bottlenecks in the AI call router.
This script simulates different types of requests and analyzes timing logs.
"""

import requests
import time
import json
import re
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5003"
TEST_CASES = [
    # Fast path - direct department request (should be very fast)
    {
        "name": "Direct Department (Pharmacy)",
        "description": "Should be fastest - direct regex match",
        "expected_timing": "< 0.1s",
        "test_type": "direct_dept"
    },
    
    # Medium path - pharmacy greeting (should be medium speed)
    {
        "name": "Pharmacy Greeting",
        "description": "Should be medium speed - goes to pharmacy greeting",
        "expected_timing": "< 0.5s", 
        "test_type": "pharmacy_greeting"
    },
    
    # Slow path - AI classification (should be slowest)
    {
        "name": "AI Classification (Unknown Item)",
        "description": "Should be slowest - requires GPT-4 classification",
        "expected_timing": "2-5s",
        "test_type": "ai_classification"
    },
    
    # TTS generation test
    {
        "name": "TTS Generation (New Text)",
        "description": "Tests TTS generation time for uncached text",
        "expected_timing": "1-3s",
        "test_type": "tts_generation"
    }
]

def test_health_check():
    """Test if the app is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed - app is running")
            return True
        else:
            print(f"❌ Health check failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed - {e}")
        return False

def analyze_timing_logs(log_file="app.log"):
    """Analyze timing logs to identify bottlenecks"""
    print(f"\n🔍 Analyzing timing logs from {log_file}...")
    
    try:
        with open(log_file, 'r') as f:
            logs = f.read()
        
        # Extract timing information
        timing_patterns = {
            "ASR Processing": r"\[TIMING\] ASR total processing time: ([\d.]+)s",
            "Language Detection": r"\[TIMING\] Language detection took ([\d.]+)s", 
            "Transcript Repair": r"\[TIMING\] Transcript repair took ([\d.]+)s",
            "Department Detection": r"\[TIMING\] Department detection took ([\d.]+)s",
            "AI Classification": r"\[TIMING\] AI classification took ([\d.]+)s",
            "TTS Generation": r"\[TIMING\] TTS generation took ([\d.]+)s",
            "TTS Total": r"total TTS time: ([\d.]+)s",
            "Generate Response": r"\[TIMING\] generate_response total time.*?([\d.]+)s",
            "Classification Total": r"total classify time: ([\d.]+)s"
        }
        
        bottlenecks = []
        for operation, pattern in timing_patterns.items():
            matches = re.findall(pattern, logs)
            if matches:
                times = [float(t) for t in matches]
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                print(f"  {operation}:")
                print(f"    Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
                print(f"    Samples: {len(matches)}")
                
                # Identify potential bottlenecks
                if avg_time > 1.0:
                    bottlenecks.append(f"{operation} (avg: {avg_time:.3f}s)")
                elif avg_time > 0.5:
                    bottlenecks.append(f"{operation} (avg: {avg_time:.3f}s) - moderate")
        
        if bottlenecks:
            print(f"\n🚨 Potential bottlenecks identified:")
            for bottleneck in bottlenecks:
                print(f"  • {bottleneck}")
        else:
            print(f"\n✅ No major bottlenecks detected - all operations under 0.5s")
            
    except FileNotFoundError:
        print(f"⚠️  Log file {log_file} not found. Make sure the app is running and generating logs.")
    except Exception as e:
        print(f"❌ Error analyzing logs: {e}")

def test_direct_department():
    """Test direct department routing (should be fastest)"""
    print(f"\n🧪 Testing: Direct Department Request")
    print(f"   Expected: Very fast (< 0.1s) - direct regex match")
    
    # This would normally be a Twilio webhook, but we can simulate the flow
    print(f"   Note: This requires an actual phone call to test properly")
    print(f"   Look for timing logs when you say 'pharmacy' or 'manager'")

def test_pharmacy_greeting():
    """Test pharmacy greeting flow (should be medium speed)"""
    print(f"\n🧪 Testing: Pharmacy Greeting Flow")
    print(f"   Expected: Medium speed (< 0.5s) - goes to pharmacy greeting")
    
    print(f"   Note: This requires an actual phone call to test properly")
    print(f"   Look for timing logs when you say 'pharmacy' and get greeting")

def test_ai_classification():
    """Test AI classification (should be slowest)"""
    print(f"\n🧪 Testing: AI Classification")
    print(f"   Expected: Slowest (2-5s) - requires GPT-4 classification")
    
    print(f"   Note: This requires an actual phone call to test properly")
    print(f"   Look for timing logs when you say an unknown item")

def test_tts_generation():
    """Test TTS generation (should be medium speed)"""
    print(f"\n🧪 Testing: TTS Generation")
    print(f"   Expected: Medium speed (1-3s) - generates new audio")
    
    print(f"   Note: This requires an actual phone call to test properly")
    print(f"   Look for timing logs when TTS generates new audio")

def run_timing_analysis():
    """Run the complete timing analysis"""
    print("🚀 AI Call Router - Response Time Analysis")
    print("=" * 50)
    
    # Check if app is running
    if not test_health_check():
        print("\n❌ Cannot proceed - app is not running")
        print("   Please start the app with: ./start_app.sh")
        return
    
    print(f"\n📊 Test Cases Overview:")
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"  {i}. {test_case['name']}")
        print(f"     {test_case['description']}")
        print(f"     Expected: {test_case['expected_timing']}")
    
    print(f"\n📋 Manual Testing Instructions:")
    print(f"   1. Make a phone call to your Twilio number")
    print(f"   2. Try each test case below")
    print(f"   3. Watch the terminal logs for timing information")
    print(f"   4. Run this script again to analyze the results")
    
    # Show test instructions
    test_direct_department()
    test_pharmacy_greeting()
    test_ai_classification()
    test_tts_generation()
    
    print(f"\n📝 How to Test:")
    print(f"   1. Call your Twilio number")
    print(f"   2. Say 'pharmacy' (fast path)")
    print(f"   3. Say 'manager' (fast path)")
    print(f"   4. Say 'banana' (AI classification - slow path)")
    print(f"   5. Say 'where are you located' (store info - medium path)")
    
    print(f"\n🔍 After Testing:")
    print(f"   Run this script again to analyze the timing logs")
    print(f"   Look for [TIMING] entries in the terminal output")
    
    # Try to analyze existing logs
    analyze_timing_logs()

if __name__ == "__main__":
    run_timing_analysis()
