from app import create_app, db
from app.models import User, Bin, Truck

def test_backend():
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("[OK] Database tables created")
        
        # Check if admin exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@smartbin.com',
                first_name='Admin',
                last_name='User',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("[OK] Admin user created (admin@smartbin.com / admin123)")
        
        # Check if bins exist
        bins = Bin.query.count()
        if bins == 0:
            # Add sample bins in Zambia
            sample_bins = [
                {'bin_code': 'BIN-001', 'location_name': 'Lusaka Main Street', 'area': 'Lusaka', 
                 'latitude': -15.3875, 'longitude': 28.3228, 'waste_type': 'General', 
                 'fill_level': 45, 'status': 'Moderate'},
                {'bin_code': 'BIN-002', 'location_name': 'Kabwe Central', 'area': 'Kabwe', 
                 'latitude': -13.1339, 'longitude': 27.8493, 'waste_type': 'Recyclable', 
                 'fill_level': 72, 'status': 'Full'},
                {'bin_code': 'BIN-003', 'location_name': 'Ndola Industrial', 'area': 'Ndola', 
                 'latitude': -11.6683, 'longitude': 27.4833, 'waste_type': 'Organic', 
                 'fill_level': 95, 'status': 'Overflow'},
            ]
            
            for bin_data in sample_bins:
                b = Bin(**bin_data)
                db.session.add(b)
            
            print(f"[OK] Added {len(sample_bins)} sample bins in Zambia")
        
        db.session.commit()
        
        # Print stats
        print("\n[STATS] Backend Stats:")
        print(f"   Users: {User.query.count()}")
        print(f"   Bins: {Bin.query.count()}")
        print(f"   Trucks: {Truck.query.count()}")
        
        print("\n[READY] Backend is ready!")
        print("\n[RUN] To run the app:")
        print("   cd C:\\Users\\Ng'andu\\OneDrive\\Desktop\\qoderrr")
        print("   flask run")
        print("   Visit: http://localhost:5000")

if __name__ == '__main__':
    test_backend()
