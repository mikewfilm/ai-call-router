# 🚀 Dashboard & Voice App Integration

This document explains how the Store Management Dashboard and AI Voice App are now integrated, allowing real-time updates between the two systems.

## 🔗 **How It Works**

### **Shared Data System**
- Both systems now use a shared data manager (`shared_data_manager.py`)
- Data is stored in JSON files in the `data/` directory
- Changes made in the dashboard immediately affect the voice app

### **API Integration**
- Voice app exposes REST API endpoints for dashboard to update data
- Dashboard calls these APIs when changes are made
- Real-time synchronization between systems

## 📁 **File Structure**

```
ai-call-router/
├── shared_data_manager.py      # Shared data management
├── app.py                      # Voice app (with API endpoints)
├── dashboard_simple.py         # Dashboard (with API calls)
├── data/                       # Shared data storage
│   ├── store_info.json
│   ├── departments.json
│   ├── inventory.json
│   ├── coupons.json
│   ├── voice_templates.json
│   ├── staff.json
│   └── settings.json
├── start_integrated.sh         # Start both systems
└── test_integration.py         # Test the integration
```

## 🚀 **Quick Start**

### **Option 1: Start Both Systems Together**
```bash
./start_integrated.sh
```

### **Option 2: Start Separately**
```bash
# Terminal 1 - Start Voice App
./start_app.sh

# Terminal 2 - Start Dashboard
./start_dashboard_simple.sh
```

## 🔧 **Available Features**

### **✅ Store Information**
- **Dashboard**: Update store name, address, phone, hours, greeting message
- **Voice App**: Uses updated greeting message and store info in responses
- **Real-time**: Changes appear immediately in voice app

### **✅ Department Management**
- **Dashboard**: Add/edit departments with phone extensions
- **Voice App**: Routes calls to updated department extensions
- **Real-time**: New departments available immediately for routing

### **✅ Inventory Management**
- **Dashboard**: Add/edit products with prices, stock levels, locations
- **Voice App**: Provides accurate inventory information to callers
- **Real-time**: Stock levels and prices updated immediately

### **✅ Coupon Management**
- **Dashboard**: Create and manage promotional offers
- **Voice App**: Offers coupons to callers based on dashboard data
- **Real-time**: New coupons available immediately

### **✅ Voice Templates**
- **Dashboard**: Create custom voice response templates
- **Voice App**: Uses templates for consistent messaging
- **Real-time**: New templates available immediately

## 🧪 **Testing the Integration**

### **1. Test API Endpoints**
```bash
python test_integration.py
```

### **2. Manual Testing**
1. Start both systems
2. Go to dashboard: http://localhost:5004
3. Login: admin / admin123
4. Update store information
5. Test voice app: http://localhost:5003/voice
6. Verify changes appear in voice responses

### **3. Test Specific Features**

#### **Store Info Update**
1. Dashboard → Store Info → Update greeting message
2. Voice app will use new greeting immediately

#### **Department Addition**
1. Dashboard → Departments → Add new department
2. Voice app will route to new department immediately

#### **Inventory Addition**
1. Dashboard → Inventory → Add new product
2. Voice app will provide info about new product immediately

## 🔌 **API Endpoints**

### **Store Information**
- `GET /api/store-info` - Get store information
- `PUT /api/store-info` - Update store information

### **Departments**
- `GET /api/departments` - Get all departments
- `POST /api/departments` - Add new department
- `PUT /api/departments/{id}` - Update department

### **Inventory**
- `GET /api/inventory` - Get all inventory items
- `POST /api/inventory` - Add new inventory item
- `PUT /api/inventory/{id}` - Update inventory item

### **Coupons**
- `GET /api/coupons` - Get all coupons
- `POST /api/coupons` - Add new coupon

### **Voice Templates**
- `GET /api/voice-templates` - Get all voice templates
- `POST /api/voice-templates` - Add new voice template

### **Settings**
- `GET /api/settings` - Get system settings
- `PUT /api/settings` - Update system settings

## 🔄 **Data Flow**

```
Dashboard (Port 5004)           Voice App (Port 5003)
     │                              │
     │ 1. User makes change         │
     │                              │
     │ 2. Update shared data        │
     │                              │
     │ 3. Call API endpoint         │
     │                              │
     │ 4. Voice app reads           │
     │    updated data              │
     │                              │
     │ 5. Changes appear in         │
     │    voice responses           │
```

## 🛠️ **Technical Details**

### **Shared Data Manager**
- Thread-safe JSON file storage
- Automatic data initialization
- Fallback to in-memory data if shared data unavailable

### **API Communication**
- RESTful endpoints with JSON data
- Error handling and logging
- Timeout protection

### **Data Synchronization**
- Immediate updates via API calls
- Persistent storage in JSON files
- Automatic data validation

## 🚨 **Troubleshooting**

### **Dashboard Not Updating Voice App**
1. Check if voice app is running on port 5003
2. Verify API endpoints are accessible
3. Check logs for error messages

### **Data Not Persisting**
1. Ensure `data/` directory exists
2. Check file permissions
3. Verify JSON file format

### **API Connection Errors**
1. Check if both systems are running
2. Verify port numbers (5003, 5004)
3. Check firewall settings

## 📈 **Future Enhancements**

### **Planned Features**
- [ ] Real-time notifications
- [ ] WebSocket communication
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] User authentication for API
- [ ] Audit logging
- [ ] Backup/restore functionality

### **Performance Optimizations**
- [ ] Data caching
- [ ] Batch updates
- [ ] Compression
- [ ] Connection pooling

## 🤝 **Support**

For issues or questions about the integration:
1. Check the logs in both systems
2. Run the integration test: `python test_integration.py`
3. Verify both systems are running on correct ports
4. Check the troubleshooting section above
