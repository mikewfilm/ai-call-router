"""
Pharmacy Management System for AI Call Router
Handles prescription refills, status checks, transfers, and pharmacist consultations
"""

import json
import os
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re

try:
    # Use shared templates managed by the dashboard if available
    from shared_data_manager import shared_data  # type: ignore
except Exception:
    shared_data = None

@dataclass
class Prescription:
    """Represents a prescription"""
    rx_number: str
    patient_name: str
    patient_phone: str
    patient_dob: str
    medication_name: str
    dosage: str
    quantity: int
    refills_remaining: int
    status: str  # "ready", "in_process", "delayed", "out_of_stock", "expired"
    prescribed_date: str
    last_filled_date: str
    next_refill_date: str
    pharmacy: str
    doctor: str
    notes: str = ""

@dataclass
class PharmacyQuery:
    """Result of a pharmacy query"""
    query_type: str  # "refill", "status", "transfer", "consultation", "general"
    found: bool
    prescriptions: List[Prescription] = None
    message: str = ""
    requires_staff: bool = False
    next_steps: List[str] = None

class PharmacyManager:
    """Manages pharmacy operations and prescription data"""
    
    def __init__(self, data_source: str = "simulated"):
        self.data_source = data_source
        self.prescriptions: Dict[str, Prescription] = {}
        self.patient_records: Dict[str, List[str]] = {}  # phone -> [rx_numbers]
        self.transfer_requests: List[Dict] = []
        
        # Initialize based on data source
        if data_source == "simulated":
            self._load_simulated_data()
        elif data_source == "json":
            self._load_json_data()
        elif data_source == "database":
            self._load_database_data()
    
    def _load_simulated_data(self):
        """Load simulated prescription data"""
        self.prescriptions = self._generate_simulated_prescriptions()
        self._build_patient_index()
    
    def _generate_simulated_prescriptions(self) -> Dict[str, Prescription]:
        """Generate realistic simulated prescription data"""
        prescriptions = {}
        
        # Common medications
        medications = [
            ("Lisinopril", "10mg", "Blood pressure medication"),
            ("Metformin", "500mg", "Diabetes medication"),
            ("Atorvastatin", "20mg", "Cholesterol medication"),
            ("Omeprazole", "20mg", "Acid reflux medication"),
            ("Amlodipine", "5mg", "Blood pressure medication"),
            ("Losartan", "50mg", "Blood pressure medication"),
            ("Simvastatin", "40mg", "Cholesterol medication"),
            ("Pantoprazole", "40mg", "Acid reflux medication"),
            ("Hydrochlorothiazide", "25mg", "Diuretic"),
            ("Metoprolol", "50mg", "Beta blocker")
        ]
        
        # Patient data
        patients = [
            ("John Smith", "555-123-4567", "1980-03-15"),
            ("Mary Johnson", "555-234-5678", "1975-07-22"),
            ("Robert Davis", "555-345-6789", "1985-11-08"),
            ("Sarah Wilson", "555-456-7890", "1990-01-30"),
            ("Michael Brown", "555-567-8901", "1978-09-12"),
            ("Lisa Garcia", "555-678-9012", "1982-04-25"),
            ("David Miller", "555-789-0123", "1970-12-03"),
            ("Jennifer Taylor", "555-890-1234", "1988-06-18"),
            ("Christopher Anderson", "555-901-2345", "1983-08-14"),
            ("Amanda Thomas", "555-012-3456", "1992-02-28")
        ]
        
        # Generate prescriptions
        for i, (med_name, dosage, notes) in enumerate(medications):
            for j, (patient_name, phone, dob) in enumerate(patients):
                rx_num = f"RX{100000 + i * 10 + j:06d}"
                
                # Randomize status and dates
                statuses = ["ready", "in_process", "delayed", "out_of_stock"]
                weights = [0.4, 0.3, 0.2, 0.1]  # More likely to be ready
                status = random.choices(statuses, weights=weights)[0]
                
                prescribed_date = datetime.now() - timedelta(days=random.randint(30, 365))
                last_filled = datetime.now() - timedelta(days=random.randint(0, 90))
                next_refill = last_filled + timedelta(days=30)
                
                prescriptions[rx_num] = Prescription(
                    rx_number=rx_num,
                    patient_name=patient_name,
                    patient_phone=phone,
                    patient_dob=dob,
                    medication_name=med_name,
                    dosage=dosage,
                    quantity=30,
                    refills_remaining=random.randint(0, 3),
                    status=status,
                    prescribed_date=prescribed_date.strftime("%Y-%m-%d"),
                    last_filled_date=last_filled.strftime("%Y-%m-%d"),
                    next_refill_date=next_refill.strftime("%Y-%m-%d"),
                    pharmacy="Main Street Pharmacy",
                    doctor=f"Dr. {random.choice(['Johnson', 'Smith', 'Davis', 'Wilson', 'Brown'])}",
                    notes=notes
                )
        
        return prescriptions
    
    def _build_patient_index(self):
        """Build patient phone to RX number mapping"""
        self.patient_records = {}
        for rx_num, prescription in self.prescriptions.items():
            phone = prescription.patient_phone
            if phone not in self.patient_records:
                self.patient_records[phone] = []
            self.patient_records[phone].append(rx_num)
    
    def handle_pharmacy_query(self, query: str) -> PharmacyQuery:
        """Handle pharmacy-related queries"""
        query_lower = query.lower()
        
        # Check for refill requests
        if any(word in query_lower for word in ["refill", "refill prescription", "refill rx", "refill medication"]) or any(phrase in query_lower for phrase in ["same as last time", "same as last", "as last time", "last time"]):
            return self._handle_refill_request(query)
        
        # Check for status requests
        elif any(word in query_lower for word in ["status", "ready", "is my prescription ready", "when will it be ready"]):
            return self._handle_status_request(query)
        
        # Check for transfer requests
        elif any(word in query_lower for word in ["transfer", "transfer prescription", "move prescription", "switch pharmacy"]):
            return self._handle_transfer_request(query)
        
        # Check for pharmacist consultation
        elif any(word in query_lower for word in ["pharmacist", "speak to pharmacist", "talk to pharmacist", "consultation", "medication question", "drug interaction", "side effect", "dosage", "food", "alcohol"]):
            return self._handle_consultation_request(query)
        
        # Check for general pharmacy questions
        elif any(word in query_lower for word in ["pharmacy", "medication", "prescription", "drug", "pill", "medicine", "delivery", "insurance", "copay", "hours", "location", "address"]):
            return self._handle_general_pharmacy_query(query)
        
        else:
            return PharmacyQuery(
                query_type="unknown",
                found=False,
                message="I'm not sure what you're asking about. Could you please clarify?",
                requires_staff=True
            )
    
    def _handle_refill_request(self, query: str) -> PharmacyQuery:
        """Handle prescription refill requests"""
        query_lower = query.lower()
        
        # Extract phone number or DOB from query
        phone_match = re.search(r'(\d{3}-\d{3}-\d{4})', query)
        # Also match 10-digit numbers without dashes
        phone_match_no_dash = re.search(r'(\d{10})', query)
        dob_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', query)
        rx_match = re.search(r'rx\s*(\d+)', query, re.I)
        
        if any(phrase in query_lower for phrase in ["same as last time", "same as last", "as last time", "last time", "refill all"]):
            # Simulate finding recent prescriptions
            recent_rxs = [rx for rx in self.prescriptions.values() 
                         if rx.refills_remaining > 0 and rx.status != "expired"]
            
            if recent_rxs:
                # Take the most recent one
                rx = recent_rxs[0]
                return PharmacyQuery(
                    query_type="refill",
                    found=True,
                    prescriptions=[rx],
                    message=f"I found your prescription for {rx.medication_name} {rx.dosage}. It has {rx.refills_remaining} refills remaining. I'll process the refill for you.",
                    requires_staff=False,
                    next_steps=["Refill will be ready in 15-20 minutes", "You'll receive a text when it's ready"]
                )
            else:
                return PharmacyQuery(
                    query_type="refill",
                    found=False,
                    message="I couldn't find any recent prescriptions with refills available. You may need to contact your doctor for a new prescription.",
                    requires_staff=True
                )
        
        elif phone_match or phone_match_no_dash:
            phone = phone_match.group(1) if phone_match else phone_match_no_dash.group(1)
            # Convert 10-digit number to phone format if needed
            if len(phone) == 10 and '-' not in phone:
                phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            if phone in self.patient_records:
                rxs = [self.prescriptions[rx_num] for rx_num in self.patient_records[phone]]
                available_rxs = [rx for rx in rxs if rx.refills_remaining > 0 and rx.status != "expired"]
                
                if available_rxs:
                    rx = available_rxs[0]  # Take the first available
                    return PharmacyQuery(
                        query_type="refill",
                        found=True,
                        prescriptions=[rx],
                        message=f"I found your prescription for {rx.medication_name} {rx.dosage}. It has {rx.refills_remaining} refills remaining. I'll process the refill for you.",
                        requires_staff=False,
                        next_steps=["Refill will be ready in 15-20 minutes", "You'll receive a text when it's ready"]
                    )
                else:
                    return PharmacyQuery(
                        query_type="refill",
                        found=False,
                        message="I found your prescriptions, but none have refills available. You may need to contact your doctor for a new prescription. Would you like me to connect you to our pharmacy staff to help with this?",
                        requires_staff=False
                    )
            else:
                return PharmacyQuery(
                    query_type="refill",
                    found=False,
                    message="I couldn't find any prescriptions with that phone number. Please check the number or provide your RX number. Would you like me to connect you to our pharmacy staff to help?",
                    requires_staff=False
                )
        
        elif rx_match:
            rx_num = f"RX{rx_match.group(1)}"
            if rx_num in self.prescriptions:
                rx = self.prescriptions[rx_num]
                if rx.refills_remaining > 0 and rx.status != "expired":
                    return PharmacyQuery(
                        query_type="refill",
                        found=True,
                        prescriptions=[rx],
                        message=f"I found your prescription for {rx.medication_name} {rx.dosage}. It has {rx.refills_remaining} refills remaining. I'll process the refill for you.",
                        requires_staff=False,
                        next_steps=["Refill will be ready in 15-20 minutes", "You'll receive a text when it's ready"]
                    )
                else:
                    return PharmacyQuery(
                        query_type="refill",
                        found=True,
                        prescriptions=[rx],
                        message=f"I found your prescription for {rx.medication_name}, but it has no refills remaining. You'll need to contact your doctor for a new prescription. Would you like me to connect you to our pharmacy staff to help with this?",
                        requires_staff=False
                    )
            else:
                return PharmacyQuery(
                    query_type="refill",
                    found=False,
                    message="I couldn't find a prescription with that RX number. Please check the number and try again. Would you like me to connect you to our pharmacy staff to help?",
                    requires_staff=False
                )
        
        else:
            return PharmacyQuery(
                query_type="refill",
                found=False,
                message="I'd be happy to help you refill your prescription. Could you please provide your RX number, phone number, or say 'refill same as last time'?",
                requires_staff=False
            )
    
    def _handle_status_request(self, query: str) -> PharmacyQuery:
        """Handle prescription status requests"""
        query_lower = query.lower()
        
        # Extract phone number or RX number
        phone_match = re.search(r'(\d{3}-\d{3}-\d{4})', query)
        rx_match = re.search(r'rx\s*(\d+)', query, re.I)
        
        if phone_match:
            phone = phone_match.group(1)
            if phone in self.patient_records:
                rxs = [self.prescriptions[rx_num] for rx_num in self.patient_records[phone]]
                in_process_rxs = [rx for rx in rxs if rx.status in ["in_process", "ready", "delayed"]]
                
                if in_process_rxs:
                    rx = in_process_rxs[0]
                    status_messages = {
                        "ready": f"Your prescription for {rx.medication_name} is ready for pickup!",
                        "in_process": f"Your prescription for {rx.medication_name} is being processed and should be ready in about 15-20 minutes.",
                        "delayed": f"Your prescription for {rx.medication_name} has been delayed. We're waiting for additional information from your doctor."
                    }
                    
                    return PharmacyQuery(
                        query_type="status",
                        found=True,
                        prescriptions=[rx],
                        message=status_messages.get(rx.status, "I found your prescription but the status is unclear."),
                        requires_staff=False
                    )
                else:
                    return PharmacyQuery(
                        query_type="status",
                        found=False,
                        message="I found your prescriptions, but none are currently being processed. Would you like to request a refill?",
                        requires_staff=False
                    )
            else:
                return PharmacyQuery(
                    query_type="status",
                    found=False,
                    message="I couldn't find any prescriptions with that phone number. Please check the number or provide your RX number. Would you like me to connect you to our pharmacy staff to help?",
                    requires_staff=False
                )
        
        elif rx_match:
            rx_num = f"RX{rx_match.group(1)}"
            if rx_num in self.prescriptions:
                rx = self.prescriptions[rx_num]
                status_messages = {
                    "ready": f"Your prescription for {rx.medication_name} is ready for pickup!",
                    "in_process": f"Your prescription for {rx.medication_name} is being processed and should be ready in about 15-20 minutes.",
                    "delayed": f"Your prescription for {rx.medication_name} has been delayed. We're waiting for additional information from your doctor.",
                    "out_of_stock": f"Your prescription for {rx.medication_name} is out of stock. We've ordered more and expect it in 2-3 business days."
                }
                
                return PharmacyQuery(
                    query_type="status",
                    found=True,
                    prescriptions=[rx],
                    message=status_messages.get(rx.status, "I found your prescription but the status is unclear."),
                    requires_staff=False
                )
            else:
                return PharmacyQuery(
                    query_type="status",
                    found=False,
                    message="I couldn't find a prescription with that RX number. Please check the number and try again. Would you like me to connect you to our pharmacy staff to help?",
                    requires_staff=False
                )
        
        else:
            return PharmacyQuery(
                query_type="status",
                found=False,
                message="I'd be happy to check your prescription status. Could you please provide your RX number or phone number?",
                requires_staff=False
            )
    
    def _handle_transfer_request(self, query: str) -> PharmacyQuery:
        """Handle prescription transfer requests"""
        query_lower = query.lower()
        
        # Extract pharmacy name if mentioned
        pharmacy_keywords = ["cvs", "walgreens", "rite aid", "walmart", "target", "kroger", "safeway"]
        from_pharmacy = None
        for keyword in pharmacy_keywords:
            if keyword in query_lower:
                from_pharmacy = keyword.title()
                break
        
        if from_pharmacy:
            return PharmacyQuery(
                query_type="transfer",
                found=True,
                message=f"I can help you transfer your prescription from {from_pharmacy}. I'll need your RX number and the name of the medication. Let me connect you to our pharmacy staff to complete the transfer.",
                requires_staff=True,
                next_steps=["Please have your RX number ready", "Transfer typically takes 24-48 hours"]
            )
        else:
            return PharmacyQuery(
                query_type="transfer",
                found=True,
                message="I can help you transfer your prescription. I'll need to know which pharmacy you're transferring from and your RX number. Let me connect you to our pharmacy staff.",
                requires_staff=True,
                next_steps=["Please have your RX number ready", "Transfer typically takes 24-48 hours"]
            )
    
    def _handle_consultation_request(self, query: str) -> PharmacyQuery:
        """Handle pharmacist consultation requests"""
        query_lower = query.lower()
        
        # Check for specific medication questions
        medication_keywords = ["interaction", "side effect", "dosage", "when to take", "how to take", "food", "alcohol"]
        has_medication_question = any(keyword in query_lower for keyword in medication_keywords)
        
        if has_medication_question:
            return PharmacyQuery(
                query_type="consultation",
                found=True,
                message="I can help with general medication questions, but for specific advice about your medications, interactions, or side effects, let me connect you to our pharmacist.",
                requires_staff=True,
                next_steps=["Pharmacist will review your medications", "Typical wait time is 5-10 minutes"]
            )
        else:
            # Use dashboard template for pharmacist connection
            try:
                if shared_data is not None:
                    message = shared_data.get_dialogue_template("pharmacy", "connect_pharmacist")
                    if not message:
                        message = shared_data.get_dialogue_template("pharmacy", "connect_pharmacy_staff")
                    if not message:
                        message = "I'll connect you to our pharmacist now."
                else:
                    message = "I'll connect you to our pharmacist now."
            except Exception:
                message = "I'll connect you to our pharmacist now."
            
            return PharmacyQuery(
                query_type="consultation",
                found=True,
                message=message,
                requires_staff=True,
                next_steps=["Pharmacist will be available shortly", "Typical wait time is 5-10 minutes"]
            )
    
    def _handle_general_pharmacy_query(self, query: str) -> PharmacyQuery:
        """Handle general pharmacy questions"""
        query_lower = query.lower()
        
        # Common pharmacy questions
        if "hours" in query_lower or "open" in query_lower:
            return PharmacyQuery(
                query_type="general",
                found=True,
                message="Our pharmacy is open Monday through Friday 9 AM to 9 PM, Saturday 9 AM to 6 PM, and Sunday 10 AM to 6 PM.",
                requires_staff=False
            )
        
        elif "location" in query_lower or "address" in query_lower or "where" in query_lower:
            return PharmacyQuery(
                query_type="general",
                found=True,
                message="We're located at 123 Main Street, downtown. We have free parking in the back lot.",
                requires_staff=False
            )
        
        elif "insurance" in query_lower or "copay" in query_lower or "cost" in query_lower:
            return PharmacyQuery(
                query_type="general",
                found=True,
                message="I can help with general insurance questions, but for specific copay or cost information, let me connect you to our pharmacy staff.",
                requires_staff=True
            )
        
        elif "delivery" in query_lower or "shipping" in query_lower:
            return PharmacyQuery(
                query_type="general",
                found=True,
                message="Yes, we offer free delivery for prescriptions within 5 miles. Delivery typically takes 2-3 hours. Would you like to set up delivery?",
                requires_staff=True
            )
        
        else:
            return PharmacyQuery(
                query_type="general",
                found=True,
                message="I can help with prescription refills, status checks, transfers, and general questions. For specific medication advice, I'll connect you to our pharmacist.",
                requires_staff=False
            )

# Global pharmacy manager instance
pharmacy_manager = PharmacyManager()

# Convenience functions for easy access
def handle_pharmacy_query(query: str) -> PharmacyQuery:
    """Handle pharmacy-related queries"""
    return pharmacy_manager.handle_pharmacy_query(query)

def get_prescription_by_rx(rx_number: str) -> Optional[Prescription]:
    """Get prescription by RX number"""
    return pharmacy_manager.prescriptions.get(rx_number)

def get_prescriptions_by_phone(phone: str) -> List[Prescription]:
    """Get prescriptions by phone number"""
    if phone in pharmacy_manager.patient_records:
        return [pharmacy_manager.prescriptions[rx_num] for rx_num in pharmacy_manager.patient_records[phone]]
    return []
