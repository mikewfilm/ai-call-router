# Pharmacy System for AI Call Router

## Overview

The pharmacy system provides comprehensive pharmacy management capabilities for the AI Call Router, allowing it to handle prescription refills, status checks, transfers, and pharmacist consultations. It's designed to work with both simulated data and real pharmacy systems.

## Features

### 💊 **Prescription Refills**
- **RX Number**: "Can you refill RX123456?"
- **Phone Number**: "Refill prescription for 555-123-4567"
- **Quick Refill**: "Refill same as last time"
- **Automatic Processing**: Handles refill requests without staff intervention

### 📋 **Status Checks**
- **Ready Status**: "Your prescription is ready for pickup!"
- **In Process**: "Being processed, ready in 15-20 minutes"
- **Delayed**: "Waiting for additional information from your doctor"
- **Out of Stock**: "Ordered more, expect it in 2-3 business days"

### 🔄 **Prescription Transfers**
- **From Other Pharmacies**: CVS, Walgreens, Rite Aid, Walmart, Target, Kroger, Safeway
- **Transfer Process**: Connects to pharmacy staff for completion
- **Timeline**: Typically takes 24-48 hours

### 👨‍⚕️ **Pharmacist Consultations**
- **Medication Questions**: Drug interactions, side effects, dosage
- **Health Advice**: General medication guidance
- **Staff Connection**: Routes to pharmacist for specific advice
- **Wait Times**: 5-10 minutes typical wait time

### 🏥 **General Pharmacy Services**
- **Hours**: Monday-Friday 9 AM-9 PM, Saturday 9 AM-6 PM, Sunday 10 AM-6 PM
- **Location**: 123 Main Street, downtown with free parking
- **Delivery**: Free delivery within 5 miles, 2-3 hour delivery time
- **Insurance**: General insurance questions and copay information

## Quick Start

### 1. Basic Usage

```python
from pharmacy_system import handle_pharmacy_query

# Handle a refill request
result = handle_pharmacy_query("I need to refill my prescription")
if result:
    print(f"Type: {result.query_type}")
    print(f"Message: {result.message}")
    print(f"Requires Staff: {result.requires_staff}")
```

### 2. Prescription Refills

```python
# Refill by RX number
result = handle_pharmacy_query("Refill RX123456")

# Refill by phone number
result = handle_pharmacy_query("Refill for 555-123-4567")

# Quick refill
result = handle_pharmacy_query("Refill same as last time")
```

### 3. Status Checks

```python
# Check status by phone
result = handle_pharmacy_query("Is my prescription ready? 555-123-4567")

# Check status by RX number
result = handle_pharmacy_query("Status of RX123456")
```

## Integration with AI Call Router

The pharmacy system is automatically integrated into the AI Call Router. When customers ask pharmacy-related questions, the system will:

1. **Detect pharmacy queries** using keyword matching
2. **Process the request** based on query type
3. **Provide direct responses** for simple queries
4. **Route to pharmacy staff** when needed

### Example Customer Interactions

**Customer**: "I need to refill my prescription"
**AI**: "To refill your prescription, I'll need either your RX number, phone number, or you can say 'refill same as last time'. Let me connect you to our pharmacy staff."

**Customer**: "Refill same as last time"
**AI**: "I found your prescription for Lisinopril 10mg. It has 3 refills remaining. I'll process the refill for you."

**Customer**: "Is my prescription ready?"
**AI**: "To check your prescription status, I'll need either your RX number or phone number. Let me connect you to our pharmacy staff."

**Customer**: "Check status for 555-123-4567"
**AI**: "Your prescription for Metformin has been delayed. We're waiting for additional information from your doctor."

**Customer**: "I want to transfer from CVS"
**AI**: "I can help you transfer your prescription from CVS. I'll need your RX number and the name of the medication. Let me connect you to our pharmacy staff to complete the transfer."

**Customer**: "I need to speak to a pharmacist about side effects"
**AI**: "I can help with general medication questions, but for specific advice about your medications, interactions, or side effects, let me connect you to our pharmacist."

**Customer**: "What are your pharmacy hours?"
**AI**: "Our pharmacy is open Monday through Friday 9 AM to 9 PM, Saturday 9 AM to 6 PM, and Sunday 10 AM to 6 PM."

## Data Structure

### Prescription
```python
@dataclass
class Prescription:
    rx_number: str                    # Unique prescription identifier
    patient_name: str                 # Patient name
    patient_phone: str                # Patient phone number
    patient_dob: str                  # Patient date of birth
    medication_name: str              # Medication name
    dosage: str                       # Dosage information
    quantity: int                     # Quantity prescribed
    refills_remaining: int            # Number of refills left
    status: str                       # ready, in_process, delayed, out_of_stock, expired
    prescribed_date: str              # Date prescribed
    last_filled_date: str             # Last fill date
    next_refill_date: str             # Next refill date
    pharmacy: str                     # Pharmacy name
    doctor: str                       # Prescribing doctor
    notes: str                        # Additional notes
```

### Pharmacy Query Results
```python
@dataclass
class PharmacyQuery:
    query_type: str                   # refill, status, transfer, consultation, general
    found: bool                       # Whether prescription was found
    prescriptions: List[Prescription]  # List of matching prescriptions
    message: str                      # Response message
    requires_staff: bool              # Whether staff intervention is needed
    next_steps: List[str]             # Next steps for customer
```

## Configuration

### Environment Variables

The pharmacy system can be configured using environment variables:

```bash
# Data source configuration
PHARMACY_DATA_SOURCE=simulated  # simulated, json, database

# Pharmacy file paths
PHARMACY_JSON_FILE=pharmacy.json
PHARMACY_EXPORT_FILE=pharmacy_export.json

# Database configuration (for future use)
PHARMACY_DB_HOST=localhost
PHARMACY_DB_PORT=5432
PHARMACY_DB_NAME=pharmacy
PHARMACY_DB_USER=user
PHARMACY_DB_PASSWORD=password
```

### Data Sources

#### 1. Simulated Data (Default)
- Built-in realistic prescription data
- Perfect for testing and demos
- No external dependencies

#### 2. JSON Files
```python
# Export current pharmacy data
pharmacy_manager.export_to_json("my_pharmacy.json")

# Import pharmacy data from file
pharmacy_manager.import_from_json("my_pharmacy.json")
```

#### 3. Database Integration (Future)
- PostgreSQL, MySQL, SQLite support
- Real-time prescription updates
- Multi-pharmacy management

## API Reference

### Core Functions

#### `handle_pharmacy_query(query: str) -> PharmacyQuery`
Handle pharmacy-related queries and return appropriate responses.

#### `get_prescription_by_rx(rx_number: str) -> Optional[Prescription]`
Get prescription details by RX number.

#### `get_prescriptions_by_phone(phone: str) -> List[Prescription]`
Get all prescriptions for a patient by phone number.

### Pharmacy Manager Methods

#### `handle_refill_request(query: str) -> PharmacyQuery`
Process prescription refill requests.

#### `handle_status_request(query: str) -> PharmacyQuery`
Check prescription status.

#### `handle_transfer_request(query: str) -> PharmacyQuery`
Handle prescription transfer requests.

#### `handle_consultation_request(query: str) -> PharmacyQuery`
Process pharmacist consultation requests.

#### `handle_general_pharmacy_query(query: str) -> PharmacyQuery`
Handle general pharmacy questions.

## Testing

Run the test script to see the pharmacy system in action:

```bash
python3 test_pharmacy_system.py
```

This will demonstrate:
- Prescription refills
- Status checks
- Transfer requests
- Pharmacist consultations
- General pharmacy questions
- AI response simulation

## Real Pharmacy Integration

To connect to a real pharmacy system:

### 1. Database Integration
```python
class DatabasePharmacyManager(PharmacyManager):
    def __init__(self, db_connection):
        self.db = db_connection
        super().__init__(data_source="database")
    
    def _load_database_data(self):
        # Load prescriptions from database
        query = "SELECT * FROM prescriptions WHERE active = true"
        results = self.db.execute(query)
        # Convert to Prescription objects
        # ...
```

### 2. API Integration
```python
class APIPharmacyManager(PharmacyManager):
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        super().__init__(data_source="api")
    
    def _load_api_data(self):
        # Load prescriptions from API
        response = requests.get(f"{self.api_url}/prescriptions", 
                              headers={"Authorization": f"Bearer {self.api_key}"})
        # Convert to Prescription objects
        # ...
```

### 3. File-based Integration
```python
# Load from CSV
import pandas as pd

def load_from_csv(filename: str):
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        prescription = Prescription(
            rx_number=row['rx_number'],
            patient_name=row['patient_name'],
            # ... other fields
        )
        pharmacy_manager.prescriptions[prescription.rx_number] = prescription
```

## Future Enhancements

### Planned Features
- **Real-time updates**: WebSocket integration for live prescription status
- **Multi-pharmacy support**: Chain-wide pharmacy management
- **Insurance integration**: Real-time copay and coverage checks
- **Delivery tracking**: Real-time delivery status updates
- **Mobile app support**: Pharmacy management on mobile devices
- **Automated refills**: Scheduled refill reminders and processing

### Performance Optimizations
- **Caching**: Redis integration for fast lookups
- **Indexing**: Advanced search indexing
- **Compression**: Efficient data storage
- **Load balancing**: Distributed pharmacy systems

## Troubleshooting

### Common Issues

#### 1. "Pharmacy system not found"
- Ensure `pharmacy_system.py` is in the same directory as `app.py`
- Check that all required dependencies are installed

#### 2. "Prescription not found" responses
- Verify the prescription exists in the pharmacy data
- Check spelling and try alternative search terms
- Use the correct phone number or RX number format

#### 3. "Status unclear" responses
- Ensure prescription status data is loaded correctly
- Check the pharmacy data source configuration

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed pharmacy operations
```

## Support

For questions or issues with the pharmacy system:

1. Check the test script for examples
2. Review the API documentation
3. Test with simulated data first
4. Verify data source configuration

The pharmacy system is designed to be robust and easy to integrate, providing a solid foundation for both testing and production use in pharmacy environments.
