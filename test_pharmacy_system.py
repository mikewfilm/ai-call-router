#!/usr/bin/env python3
"""
Test script for the pharmacy system
Demonstrates pharmacy queries and responses
"""

from pharmacy_system import handle_pharmacy_query, pharmacy_manager

def test_pharmacy_queries():
    """Test various pharmacy queries"""
    
    print("💊 Testing Pharmacy System")
    print("=" * 50)
    
    # Test 1: Prescription Refills
    print("\n1. Testing Prescription Refills:")
    refill_queries = [
        "I need to refill my prescription",
        "Can you refill RX123456?",
        "Refill same as last time",
        "I need to refill my medication, my phone number is 555-123-4567",
        "Refill prescription for 555-234-5678"
    ]
    
    for query in refill_queries:
        print(f"\nQuery: {query}")
        result = handle_pharmacy_query(query)
        if result:
            print(f"  Type: {result.query_type}")
            print(f"  Found: {result.found}")
            print(f"  Message: {result.message}")
            print(f"  Requires Staff: {result.requires_staff}")
            if result.next_steps:
                print(f"  Next Steps: {', '.join(result.next_steps)}")
        else:
            print("  No result")
    
    # Test 2: Status Checks
    print("\n2. Testing Status Checks:")
    status_queries = [
        "Is my prescription ready?",
        "What's the status of RX123456?",
        "When will my prescription be ready?",
        "Check status for 555-123-4567"
    ]
    
    for query in status_queries:
        print(f"\nQuery: {query}")
        result = handle_pharmacy_query(query)
        if result:
            print(f"  Type: {result.query_type}")
            print(f"  Found: {result.found}")
            print(f"  Message: {result.message}")
            print(f"  Requires Staff: {result.requires_staff}")
        else:
            print("  No result")
    
    # Test 3: Transfers
    print("\n3. Testing Prescription Transfers:")
    transfer_queries = [
        "I want to transfer my prescription from CVS",
        "Transfer prescription from Walgreens",
        "Move my prescription to this pharmacy",
        "Switch pharmacy"
    ]
    
    for query in transfer_queries:
        print(f"\nQuery: {query}")
        result = handle_pharmacy_query(query)
        if result:
            print(f"  Type: {result.query_type}")
            print(f"  Found: {result.found}")
            print(f"  Message: {result.message}")
            print(f"  Requires Staff: {result.requires_staff}")
            if result.next_steps:
                print(f"  Next Steps: {', '.join(result.next_steps)}")
        else:
            print("  No result")
    
    # Test 4: Pharmacist Consultations
    print("\n4. Testing Pharmacist Consultations:")
    consultation_queries = [
        "I need to speak to a pharmacist",
        "I have a question about drug interactions",
        "What are the side effects of my medication?",
        "Can I take this with food?",
        "Talk to pharmacist about dosage"
    ]
    
    for query in consultation_queries:
        print(f"\nQuery: {query}")
        result = handle_pharmacy_query(query)
        if result:
            print(f"  Type: {result.query_type}")
            print(f"  Found: {result.found}")
            print(f"  Message: {result.message}")
            print(f"  Requires Staff: {result.requires_staff}")
            if result.next_steps:
                print(f"  Next Steps: {', '.join(result.next_steps)}")
        else:
            print("  No result")
    
    # Test 5: General Pharmacy Questions
    print("\n5. Testing General Pharmacy Questions:")
    general_queries = [
        "What are your pharmacy hours?",
        "Where is the pharmacy located?",
        "Do you accept my insurance?",
        "Do you offer delivery?",
        "What's the copay for prescriptions?"
    ]
    
    for query in general_queries:
        print(f"\nQuery: {query}")
        result = handle_pharmacy_query(query)
        if result:
            print(f"  Type: {result.query_type}")
            print(f"  Found: {result.found}")
            print(f"  Message: {result.message}")
            print(f"  Requires Staff: {result.requires_staff}")
        else:
            print("  No result")

def test_pharmacy_response_simulation():
    """Simulate how the AI would respond to pharmacy queries"""
    
    print("\n🤖 Simulating AI Pharmacy Responses")
    print("=" * 50)
    
    # Simulate the _handle_pharmacy_query function
    def simulate_pharmacy_response(query: str) -> str:
        result = handle_pharmacy_query(query)
        if not result:
            return None
        
        if result.requires_staff:
            return f"{result.message} Let me connect you to our pharmacy staff."
        else:
            return result.message
    
    # Test queries
    test_queries = [
        "I need to refill my prescription",
        "Is my prescription ready?",
        "I want to transfer from CVS",
        "I need to speak to a pharmacist about side effects",
        "What are your pharmacy hours?",
        "Refill same as last time",
        "Check status for 555-123-4567",
        "Do you offer delivery?"
    ]
    
    for query in test_queries:
        print(f"\nCustomer: {query}")
        response = simulate_pharmacy_response(query)
        if response:
            print(f"AI: {response}")
        else:
            print("AI: (Would route to department instead)")

def test_prescription_data():
    """Test the simulated prescription data"""
    
    print("\n📋 Testing Prescription Data")
    print("=" * 50)
    
    # Show some sample prescriptions
    print("Sample Prescriptions:")
    count = 0
    for rx_num, prescription in pharmacy_manager.prescriptions.items():
        if count < 5:  # Show first 5
            print(f"\nRX: {prescription.rx_number}")
            print(f"  Patient: {prescription.patient_name}")
            print(f"  Medication: {prescription.medication_name} {prescription.dosage}")
            print(f"  Status: {prescription.status}")
            print(f"  Refills: {prescription.refills_remaining}")
            print(f"  Phone: {prescription.patient_phone}")
            count += 1
        else:
            break
    
    # Show patient records
    print(f"\nPatient Records: {len(pharmacy_manager.patient_records)} patients")
    for phone, rx_numbers in list(pharmacy_manager.patient_records.items())[:3]:
        print(f"  {phone}: {len(rx_numbers)} prescriptions")

if __name__ == "__main__":
    test_pharmacy_queries()
    test_pharmacy_response_simulation()
    test_prescription_data()
