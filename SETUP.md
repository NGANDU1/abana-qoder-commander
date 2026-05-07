# SmartBin - Smart Waste Management System
## Setup Instructions

### 1. Install Dependencies
```bash
cd C:\Users\Ng'andu\OneDrive\Desktop\qoderrrr
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 2. Get Google Maps API Key (FREE)
1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable "Maps JavaScript API":
   - Go to "APIs & Services" > "Library"
   - Search for "Maps JavaScript API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key
5. **IMPORTANT**: Restrict the API key:
   - Click on the API key you just created
   - Under "API restrictions", select "Restrict key"
   - Check "Maps JavaScript API"
   - Click "Save"

### 3. Add Your API Key
Open `smart-waste-system\landing.html`, find this line (around line 10):
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY&callback=initMap" async defer></script>
```

Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual key:
```html
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyA...YOUR_KEY...&callback=initMap" async defer></script>
```

### 4. Run the Application
```bash
cd C:\Users\Ng'andu\OneDrive\Desktop\qoderrrr
.\venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5000
```

Or simply:
```bash
cd C:\Users\Ng'andu\OneDrive\Desktop\qoderrrr
.\venv\Scripts\flask.exe run
```

### 5. Access the Application
- **Landing Page**: http://localhost:5000/
- **Login Page**: http://localhost:5000/auth/login
- **Admin Dashboard**: http://localhost:5000/admin/ (login as admin@smartbin.com / admin123)
- **Citizen Dashboard**: http://localhost:5000/user/ (create a citizen account)
- **Driver Dashboard**: http://localhost:5000/collector/ (create a driver account)

### 6. Test API Endpoints
```bash
# Get all bins
curl http://localhost:5000/api/bins

# Get admin stats
curl http://localhost:5000/api/admin/stats

# Get fleet status
curl http://localhost:5000/api/admin/fleet
```

## Features Implemented

### Frontend (smart-waste-system/)
- ✅ Modern landing page with Google Maps (Zambia locations)
- ✅ Role-based dashboards (Citizen, Driver, Admin)
- ✅ Leaflet.js maps with real-time bin locations
- ✅ Chart.js analytics
- ✅ Responsive design
- ✅ Green eco-friendly theme

### Backend (Flask)
- ✅ User authentication (Citizen, Driver, Admin roles)
- ✅ IoT sensor API endpoint (`/api/sensor/update`)
- ✅ Pickup request system
- ✅ Complaint reporting with photo upload
- ✅ Real-time bin monitoring
- ✅ Route optimization
- ✅ Fleet management
- ✅ Payment integration
- ✅ Admin dashboard API

## Database Models
- **User**: Citizen, Driver, Admin roles
- **Bin**: Smart bins with GPS, fill level, weight sensors
- **Truck**: Fleet vehicles with GPS tracking
- **Collection**: Pickup requests and confirmations
- **Alert**: Automatic overflow/battery alerts
- **Payment**: Online payment processing
- **BinReport**: Citizen complaint reports

## File Structure
```
qoderrrr/
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── models.py          # Database models
│   ├── config.py          # Configuration
│   ├── extensions.py      # Flask extensions
│   └── blueprints/
│       ├── auth/           # Login/Register
│       ├── public/         # Landing page, maps
│       ├── user/           # Citizen dashboard
│       ├── collector/      # Driver dashboard
│       ├── admin/          # Admin dashboard
│       └── api/             # REST API endpoints
├── smart-waste-system/      # NEW Frontend UI
│   ├── index.html          # Login/Register
│   ├── landing.html        # Landing page with Google Maps
│   ├── citizen.html        # Citizen dashboard
│   ├── driver.html         # Driver dashboard
│   ├── admin.html         # Admin dashboard
│   ├── css/
│   ├── js/
│   └── images/             # Your uploaded images
└── venv/                    # Python virtual environment
```

## Next Steps
1. Get your FREE Google Maps API key (5 minutes)
2. Add the key to `landing.html`
3. Run `flask run`
4. Visit http://localhost:5000/

**Enjoy your Smart Waste Management System!** 🚀♻️
