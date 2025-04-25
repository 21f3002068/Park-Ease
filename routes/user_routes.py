from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

user_bp = Blueprint('user', __name__)



@user_bp.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        address = request.form.get('address')
        pin = request.form.get('pin')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('user/user_signup.html')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('User already exists with this email.', 'error')
            return render_template('user/user_signup.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            gender=gender,
            phone=phone,
            password=hashed_password,
            address=address,
            pin=pin
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('user.user_login'))
        
    return render_template('user/user_signup.html')




@user_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')

        # Try fetching by email or username
        user = User.query.filter(
            (User.email == username_or_email) | (User.username == username_or_email)
        ).first()

        if user and check_password_hash(user.password, password):
            # Store user info in session or however you manage auth
            login_user(user)
            return redirect(url_for('user.dashboard'))  # Redirect to user dashboard or homepage
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('user/user_login.html')

    return render_template('user/user_login.html')



def calculate_duration(start_time):
    now = datetime.utcnow()
    delta = now - start_time
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{hours}h {minutes}m"

@user_bp.route('/dashboard')
def dashboard():
    current_parking = Reservation.query.filter_by(
        user_id=current_user.id,
        leaving_timestamp=None
    ).first()
    
    parking_history = Reservation.query.filter_by(
        user_id=current_user.id
    ).filter(
        Reservation.leaving_timestamp.isnot(None)
    ).order_by(
        Reservation.parking_timestamp.desc()
    ).limit(5).all()
    
    return render_template(
        'user/dashboard.html',
        current_parking=current_parking,
        parking_history=parking_history,
        calculate_duration=calculate_duration  # Helper function you need to create
    )




@user_bp.route('/park_out/<int:reservation_id>', methods=['POST'])
@login_required
def park_out(reservation_id):
    # Get the reservation
    reservation = Reservation.query.filter_by(
        id=reservation_id,
        user_id=current_user.id,
        leaving_timestamp=None  # Only if not already checked out
    ).first_or_404()
    
    try:
        # Calculate parking duration and cost
        now = datetime.utcnow()
        parking_duration = now - reservation.parking_timestamp
        hours_parked = max(1, parking_duration.total_seconds() / 3600)  # Minimum 1 hour
        
        # Update reservation
        reservation.leaving_timestamp = now
        reservation.parking_cost = hours_parked * reservation.spot.lot.price_per_hour
        reservation.status = 'Completed'
        
        # Free up the parking spot
        reservation.spot.status = 'A'  # Available
        
        db.session.commit()
        
        flash(f'Park out successful. Total charge: ₹{reservation.parking_cost:.2f}', 'success')
        return redirect(url_for('user.bookings'))
    
    except Exception as e:
        db.session.rollback()
        flash('Error processing park out. Please try again.', 'error')
        return redirect(url_for('user.dashboard'))

@user_bp.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    # Get return_to parameter for redirect after adding
    return_to = request.args.get('return_to')
    
    if request.method == 'POST':
        # Get form data
        vehicle_name = request.form.get('vehicle_name')
        license_plate = request.form.get('license_plate').upper().strip()  # Normalize plate
        color = request.form.get('color')
        
        # Basic validation
        errors = []
        
        if not license_plate:
            errors.append('License plate is required')
        elif len(license_plate) < 3:
            errors.append('License plate is too short')
            
            
        if not color:
            errors.append('Color is required')
            
        # Check if license plate already exists
        existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        if existing_vehicle:
            errors.append('This license plate is already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            try:
                # Create new vehicle
                new_vehicle = Vehicle(
                    vehicle_name=vehicle_name or f"{current_user.firstname}'s Car",
                    license_plate=license_plate,
                    color=color,
                    user_id=current_user.id
                )
                
                db.session.add(new_vehicle)
                db.session.commit()
                
                flash('Vehicle added successfully!', 'success')
                
                # Redirect to booking if return_to was provided
                if return_to:
                    return redirect(url_for('user.book_parking', lot_id=return_to))
                return redirect(url_for('user.profile'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error adding vehicle. Please try again.', 'error')
    
    # Render form (GET request or form errors)
    return render_template('partials/_add_new_vehicle.html',
                         return_to=return_to,
                         vehicle_types=['Car', 'Motorcycle', 'Truck', 'SUV', 'Van'])




@user_bp.route('/search', methods=['GET', 'POST'])
def search():
    return render_template('user/search.html')



@user_bp.route('/parking_locations')
def locations():
    # Get all locations with their parking lots in one query
    all_locations = Location.query.options(
        joinedload(Location.parking_lots)
    ).all()
    
    # Get all lot IDs in one list
    lot_ids = [lot.id for loc in all_locations for lot in loc.parking_lots]
    
    # Count available spots per lot in one query
    spots_count = dict(db.session.query(
        ParkingSpot.lot_id,
        func.count(ParkingSpot.id)
    ).filter(
        ParkingSpot.lot_id.in_(lot_ids),
        ParkingSpot.status == 'A'
    ).group_by(ParkingSpot.lot_id).all())
    
    # Prepare data for template
    location_data = []
    for loc in all_locations:
        location_data.append({
            "location": loc,
            "lots": loc.parking_lots,
            "spots_count": spots_count
        })
    
    return render_template('user/locations.html',
                         location_data=location_data,
                         spots_count=spots_count,
                         available_spots_count=lambda lot: spots_count.get(lot.id, 0))
    
    
    

def available_spots_count(lot):
    return ParkingSpot.query.filter_by(
        lot_id=lot.id,
        status='A'  # 'A' for Available
    ).count()

@user_bp.route('/parking/<int:lot_id>')
def view_parking_details(lot_id):
    # Detailed view endpoint
    return None




@user_bp.route('/book/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def book_parking(lot_id):
    # Get the parking lot with available spots
    parking_lot = ParkingLot.query.options(
        joinedload(ParkingLot.spots)
    ).get_or_404(lot_id)
    
    # Check if parking lot is active
    if not parking_lot.is_active:
        flash('This parking lot is currently unavailable', 'error')
        return redirect(url_for('user.locations'))
    
    # Get user's vehicles
    vehicles = current_user.vehicles
    
    if not vehicles:
        flash('You need to add a vehicle before booking', 'error')
        return redirect(url_for('user.add_vehicle'))
    
    # Find available spots
    available_spots = [spot for spot in parking_lot.spots if spot.status == 'A']
    
    if not available_spots:
        flash('No available spots in this parking lot', 'error')
        return redirect(url_for('user.locations'))
    
    if request.method == 'POST':
        # Get form data
        vehicle_id = request.form.get('vehicle_id')
        hours = int(request.form.get('hours', 1))
        
        # Validate vehicle belongs to user
        vehicle = next((v for v in vehicles if v.id == int(vehicle_id)), None)
        if not vehicle:
            flash('Invalid vehicle selected', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        
        # Validate hours (1-24)
        if hours < 1 or hours > 24:
            flash('Booking duration must be between 1-24 hours', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        
        # Get first available spot
        spot = available_spots[0]
        
        try:
            # Calculate parking cost
            cost = parking_lot.price_per_hour * hours
            
            # Create reservation
            reservation = Reservation(
                spot_id=spot.id,
                user_id=current_user.id,
                vehicle_id=vehicle.id,
                parking_timestamp=datetime.utcnow(),
                parking_cost=cost
            )
            
            # Update spot status
            spot.status = 'O'  # Occupied
            
            # Commit to database
            db.session.add(reservation)
            db.session.commit()
            
            flash(f'Booking confirmed for {hours} hour(s). Total: ₹{cost:.2f}', 'success')
            return redirect(url_for('user.bookings'))
            
        except Exception as e:
            db.session.rollback()
            flash('Booking failed. Please try again.', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
    
    # GET request - show booking form
    return render_template('partials/_book_parking.html',
                         parking_lot=parking_lot,
                         vehicles=vehicles,
                         available_spots_count=len(available_spots))



@user_bp.route('/favorites/<int:lot_id>', methods=['POST', 'DELETE'])
def manage_favorites(lot_id):
    # Favorite management endpoint
    return None


from sqlalchemy import or_


from datetime import datetime, timedelta
from sqlalchemy import or_, and_

@user_bp.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    now = datetime.utcnow()
    
    # 1. Active Bookings (currently parked vehicles)
    active_bookings = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.parking_timestamp <= now,
        Reservation.leaving_timestamp == None
    ).options(
        joinedload(Reservation.spot).joinedload(ParkingSpot.lot),
        joinedload(Reservation.vehicle)
    ).all()
    
    # 2. Pending Requests (future bookings)
    pending_requests = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.parking_timestamp > now,
        Reservation.spot_id == None  # Not assigned a spot yet
    ).options(
        joinedload(Reservation.vehicle)
    ).all()
    
    # 3. Cancelled/Rejected Bookings
    cancelled_bookings = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        or_(
            Reservation.status.in_(['Cancelled', 'Rejected']),
            and_(
                Reservation.parking_timestamp < now - timedelta(minutes=15),
                Reservation.spot_id == None
            )
        )
    ).options(
        joinedload(Reservation.spot).joinedload(ParkingSpot.lot),
        joinedload(Reservation.vehicle)
    ).all()
    
    # 4. Parking History (completed bookings)
    parking_history = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.leaving_timestamp != None
    ).options(
        joinedload(Reservation.spot).joinedload(ParkingSpot.lot),
        joinedload(Reservation.vehicle),
        joinedload(Reservation.review)
    ).order_by(Reservation.leaving_timestamp.desc()).limit(20).all()
    
    return render_template('user/bookings.html',
        active_bookings=active_bookings,
        pending_requests=pending_requests,
        cancelled_bookings=cancelled_bookings,
        parking_history=parking_history,
        now=now)





from flask_login import current_user
from sqlalchemy import extract, func
from collections import defaultdict
from datetime import datetime
import json


@user_bp.route('/stats', methods=['GET'])
@login_required
def statistics():
    pending_count = Reservation.query.filter_by(status='Pending').count()
    confirmed_count = Reservation.query.filter_by(status='Confirmed').count()
    completed_count = Reservation.query.filter_by(status='Completed').count()
    cancelled_count = Reservation.query.filter_by(status='Cancelled').count()

    status_data = {
        'pending': pending_count,
        'confirmed': confirmed_count,
        'completed': completed_count,
        'cancelled': cancelled_count
    }
    
    spending_data = db.session.query(
        ParkingLot.prime_location_name,
        func.sum(Reservation.parking_cost).label('total_spending')
    ).join(Reservation, ParkingLot.id == Reservation.spot_id).group_by(ParkingLot.id).all()

    # Prepare data to send to the frontend
    locations = [item[0] for item in spending_data]  # List of parking lot names
    total_spending = [item[1] for item in spending_data]  # Corresponding total spending per location

    # Prepare the data to send to the template
    spending_info = {
        'locations': locations,
        'total_spending': total_spending
    }

    frequent_locations = db.session.query(
        ParkingLot.prime_location_name,
        func.count(Reservation.id).label('reservation_count')
    ).join(ParkingSpot, Reservation.spot_id == ParkingSpot.id) \
     .join(ParkingLot, ParkingSpot.lot_id == ParkingLot.id) \
     .group_by(ParkingLot.id) \
     .order_by(func.count(Reservation.id).desc()) \
     .all()
     
    locations = [item[0] for item in frequent_locations]
    reservation_counts = [item[1] for item in frequent_locations]

    # Prepare the data to send to the template
    frequent_info = {
        'locations': locations,
        'reservation_counts': reservation_counts
    }
    
    user_vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    
    # Query the number of reservations per vehicle
    vehicle_usage = db.session.query(
        Vehicle.vehicle_name,
        func.count(Reservation.id).label('reservation_count')
    ).join(Reservation, Reservation.vehicle_id == Vehicle.id) \
     .filter(Reservation.user_id == current_user.id) \
     .group_by(Vehicle.id) \
     .order_by(func.count(Reservation.id).desc()) \
     .all()

    # Prepare data for the frontend
    vehicle_names = [item[0] for item in vehicle_usage]
    reservation_counts = [item[1] for item in vehicle_usage]

    # Prepare the data to send to the template
    vehicle_info = {
        'vehicle_names': vehicle_names,
        'reservation_counts': reservation_counts
    }

    return render_template('user/statistics.html',
                           status_data=status_data, 
                           spending_info=spending_info, 
                           frequent_info=frequent_info,
                           vehicle_info=vehicle_info)




@user_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template('user/profile.html')