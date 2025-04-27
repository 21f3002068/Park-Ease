from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort, jsonify
from model import *
import logging
import uuid
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

user_bp = Blueprint('user', __name__)



@user_bp.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('user/user_signup.html')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('User already exists with this email.', 'error')
            return render_template('user/user_signup.html')
        
        base_username = email.split('@')[0]
        username = base_username
        counter = 1

        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
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
    now = datetime.now()  # not utcnow()
    delta = now - start_time
    total_minutes = delta.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours}h {minutes}m"




@user_bp.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now()
    current_parking = Reservation.query.filter_by(
        user_id=current_user.id,
        leaving_timestamp=None,
        status="Parked"
    ).first()
    
    scheduled_upnext = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.parking_timestamp == None, 
        Reservation.leaving_timestamp == None,
        Reservation.status == "Confirmed" 
    ).first()
    
    
    parking_history = Reservation.query.filter_by(
        user_id=current_user.id
    ).filter(
        Reservation.leaving_timestamp.isnot(None)
    ).order_by(
        Reservation.parking_timestamp.desc()
    ).limit(5).all()
    
    user = current_user
    milestones = 5
    completed = 0

    if user.firstname and user.lastname:
        completed += 1
    if user.gender:
        completed += 1
    if user.phone:
        completed += 1
    if user.address and user.pin:
        completed += 1
    if user.vehicles and len(user.vehicles) > 0:
        completed += 1

    profile_completion = int((completed / milestones) * 100)
    
    return render_template(
        'user/dashboard.html',
        current_parking=current_parking,
        scheduled_upnext=scheduled_upnext,
        parking_history=parking_history,
        profile_completion=profile_completion,
        user=user,
        calculate_duration=calculate_duration  # Helper function you need to create
    )


@user_bp.route('/park/<int:booking_id>', methods=['POST'])
@login_required
def park(booking_id):
    booking = Reservation.query.get_or_404(booking_id)
    current_time = datetime.now()

    # Check if current time is close enough to expected arrival (say ±10 min flexibility)
    arrival_time = booking.expected_arrival

    if abs((current_time - arrival_time).total_seconds()) > 600:  # 600 seconds = 10 minutes
        flash('Your vehicle is not expected for parking yet.', 'warning')
        return redirect(url_for('user.dashboard'))

    # Set actual parking
    booking.parking_timestamp = current_time
    booking.status = 'Parked'
    db.session.commit()

    flash('You have successfully parked your vehicle.', 'success')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/park_out/<int:reservation_id>', methods=['POST'])
@login_required
def park_out(reservation_id):
    # Get the reservation
    reservation = Reservation.query.filter_by(
        id=reservation_id,
        user_id=current_user.id,
        leaving_timestamp=None,
        status="Parked"
    ).first_or_404()
    
    try:
        # Only database operations inside try
        now = datetime.now()
        parking_duration = now - reservation.parking_timestamp
        hours_parked = max(1, parking_duration.total_seconds() / 3600)

        reservation.leaving_timestamp = now
        reservation.parking_cost = hours_parked * reservation.spot.lot.price_per_hour
        reservation.status = 'Parked Out'

        reservation.spot.status = 'A'

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash('Error processing park out. Please try again.', 'error')
        return redirect(url_for('user.dashboard'))
    
    # Now safely flash success after commit
    flash(f'Park out successful. Total charge: ₹{reservation.parking_cost:.2f}', 'success')
    return redirect(url_for('user.add_review', reservation_id=reservation.id))


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
    
    # Calculate total parking spots for each location
    location_data = []
    for loc in all_locations:
        # Calculate total parking spots for the location (sum of parking spots in all lots)
        total_parking_spots = sum(lot.available_spots for lot in loc.parking_lots)
        
        location_data.append({
            "location": loc,
            "lots": loc.parking_lots,
            "spots_count": spots_count,
            "total_parking_spots": total_parking_spots  # Add the total parking spots
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

    parking_lot = ParkingLot.query.get(lot_id)
    all_locations = Location.query.options(
        joinedload(Location.parking_lots)
    ).all()
    
    lot_ids = [lot.id for loc in all_locations for lot in loc.parking_lots]

    
    if not parking_lot:
        return "Parking lot not found", 404
    
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

    
    return render_template('partials/_view_parking_details.html', 
                        lot=parking_lot,
                        location_data=location_data,
                        spots_count=spots_count,
                        available_spots_count=lambda lot: spots_count.get(lot.id, 0))




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
        expected_arrival = request.form.get('expected_arrival')
        expected_departure = request.form.get('expected_departure')
        
        # Validate vehicle belongs to user
        vehicle = next((v for v in vehicles if v.id == int(vehicle_id)), None)
        if not vehicle:
            flash('Invalid vehicle selected', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        
        
        # Parse expected_arrival and expected_departure
        try:
            expected_arrival_time = datetime.strptime(expected_arrival, '%H:%M').time()
            expected_departure_time = datetime.strptime(expected_departure, '%H:%M').time()
        except ValueError:
            flash('Invalid time format', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        
        
        # Validate arrival before departure
        if expected_arrival_time >= expected_departure_time:
            flash('Departure time must be after arrival time.', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        
        if (expected_arrival_time < parking_lot.available_from or
            expected_departure_time > parking_lot.available_to):
            flash(f'Booking must be between {parking_lot.available_from.strftime("%I:%M %p")} and {parking_lot.available_to.strftime("%I:%M %p")}.', 'error')
            return redirect(url_for('user.book_parking', lot_id=lot_id))

        today = datetime.today().date()
        
        expected_arrival_time = datetime.combine(today, expected_arrival_time)
        expected_departure_time = datetime.combine(today, expected_departure_time)

        conflict_found = False
        for spot in available_spots:
            for reservation in spot.reservations:
                if reservation.status != 'Cancelled':
                    # Overlapping check
                    if not (expected_departure_time <= reservation.parking_timestamp or expected_arrival_time >= reservation.leaving_timestamp):
                        conflict_found = True
                        break
            if not conflict_found:
                # Found an available spot without conflict
                available_spot = spot
                status = "Confirmed"  #I added this line
                break
        
        if conflict_found or not available_spots:
            flash('No available spots for the selected time range. Your booking is pending.', 'error')
            status="Pending" # And I added this line
        
        try:
            # Calculate parking cost
            total_hours = (expected_departure_time - expected_arrival_time).total_seconds() / 3600
            cost = parking_lot.price_per_hour * total_hours
                        
            vehicle_number = vehicle.license_plate[-2:].upper()  # get last 2 characters of the plate
            booking_id = f"BK-{vehicle_number}-{current_user.id}-{uuid.uuid4().hex[:3].upper()}"
            
            # Create reservation
            reservation = Reservation(
                spot_id=available_spot.id,
                user_id=current_user.id,
                vehicle_id=vehicle.id,
                expected_arrival=expected_arrival_time,
                expected_departure=expected_departure_time,
                parking_cost=cost,
                status=status, # Earlier it was taking status = "Confirmed" directly without any checks
                booking_id=booking_id
            )
            
            # Update spot status temporarily if you want (optional, based on your system)
            available_spot.status = 'O'  # 'O' for Occupied, assuming that's your status convention
            
            # Commit to database
            db.session.add(reservation)
            db.session.commit()
            
            
            flash(f'Booking confirmed! Expected cost: ₹{cost:.2f}', 'success')
            return redirect(url_for('user.bookings'))
            
        except Exception as e:
            db.session.rollback()
            # flash(f'Booking failed. Please try again. Error: {str(e)}', 'error')
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
    now = datetime.now()
    current_parking = Reservation.query.filter_by(
        user_id=current_user.id,
        leaving_timestamp=None,
        status="Parked" 
    ).first()
    # 1. Active Bookings (currently parked vehicles)
    active_bookings = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.parking_timestamp == None, 
        Reservation.leaving_timestamp == None,
        Reservation.status == "Confirmed" 
    ).options(
        joinedload(Reservation.spot).joinedload(ParkingSpot.lot),
        joinedload(Reservation.vehicle)
    ).all()
    
    # 2. Pending Requests 
    pending_requests = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.parking_timestamp > now,
        Reservation.spot_id == None,  # Not assigned a spot yet
        Reservation.status == "Pending"

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
        Reservation.leaving_timestamp != None,
        Reservation.status == "Parked Out"
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
        current_parking=current_parking,
        now=now)



@user_bp.route('dashboard/bookings/booking_details:<string:booking_id>', methods=['GET', 'POST'])
def booking_details(booking_id):
    reservation = Reservation.query.filter_by(booking_id=booking_id).first()

    if reservation:

        return render_template('partials/_view_booking_details.html', reservation=reservation)
    else:

        flash('Booking not found', 'error')
        return redirect(url_for('user.bookings')) 



@user_bp.route('/cancel_booking/<booking_id>')
def cancel_booking(booking_id):
    reservation = Reservation.query.filter_by(booking_id=booking_id, user_id=current_user.id).first()

    if reservation:
        if reservation.status in ['Confirmed', 'Pending']:
            reservation.status = 'Cancelled'
            reservation.cancellation_reason = "Cancelled by user."
            db.session.commit()
            flash('Your booking has been cancelled.', 'success')
        else:
            flash('Booking cannot be cancelled.', 'danger')
    else:
        flash('Reservation not found.', 'danger')

    return redirect(url_for('user.bookings'))


@user_bp.route('/delete_booking/<booking_id>')
def delete_booking(booking_id):
    reservation = Reservation.query.filter_by(booking_id=booking_id, user_id=current_user.id).first()

    if reservation:
        if reservation.status == 'Parked Out':
            db.session.delete(reservation)
            db.session.commit()
            flash('Booking deleted successfully.', 'success')
        else:
            flash('Only completed (Parked Out) bookings can be deleted.', 'danger')
    else:
        flash('Reservation not found.', 'danger')

    return redirect(url_for('user.bookings'))


@user_bp.route('/add_review/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def add_review(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    # Check if the reservation belongs to the current user
    if reservation.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('user.profile'))

    # If review already exists, prevent double review
    if reservation.review:
        flash('Review already submitted.', 'info')
        return redirect(url_for('user.profile'))

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating:
            flash('Rating is required!', 'danger')
            return render_template('partials/_add_parking_review.html', reservation=reservation)

        new_review = Review(
            reservation_id=reservation.id,
            rating=int(rating),
            comment=comment
        )

        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('user.profile'))

    return render_template('partials/_add_parking_review.html', reservation=reservation)




@user_bp.route('/stats', methods=['GET'])
@login_required
def statistics():
    pending_count = Reservation.query.filter_by(status='Pending').count()
    confirmed_count = Reservation.query.filter_by(status='Confirmed').count()
    parked_out_count = Reservation.query.filter_by(status='Parked Out').count()
    combined_count = Reservation.query.filter(
        or_(
            Reservation.status == 'Cancelled',
            Reservation.status == 'Rejected'
        )
    ).count()

    status_data = {
        'pending': pending_count,
        'confirmed': confirmed_count,
        'parked_out': parked_out_count,
        'cancelled_rejected': combined_count
        
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




@user_bp.route('/profile')
@login_required
def profile():
    user_reviews = (
        db.session.query(Review)
        .join(Review.reservation)
        .filter(Reservation.user_id == current_user.id)
        .options(
            joinedload(Review.reservation)
            .joinedload(Reservation.spot)
            .joinedload(ParkingSpot.lot)  # not Spot.lot
        )
        .order_by(Review.created_at.desc())
        .all()
    )
    
    favorite_lots = (
        db.session.query(ParkingLot)
        .join(Favorite, Favorite.lot_id == ParkingLot.id)
        .filter(Favorite.user_id == current_user.id)
        .all()
    )
    return render_template('user/profile.html', user=current_user, user_reviews=user_reviews, favorites=favorite_lots)


@user_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        gender = request.form['gender']
        phone = request.form['phone']
        address = request.form['address']
        pin = request.form['pin']

        # Handle password change (only update if a new password is provided)
        if password:
            hashed_password = generate_password_hash(password)
        else:
            hashed_password = current_user.password  # Keep the existing password

        # Update the user profile
        current_user.email = email
        current_user.password = hashed_password
        current_user.firstname = firstname
        current_user.lastname = lastname
        current_user.gender = gender
        current_user.phone = phone
        current_user.address = address
        current_user.pin = pin

        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))

    # Render the profile edit page with user data
    return render_template('partials/_edit_user_profile.html', user=current_user)



@user_bp.route('/edit_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        vehicle.vehicle_name = request.form['vehicle_name']
        vehicle.license_plate = request.form['license_plate']
        vehicle.color = request.form['color']

        db.session.commit()
        return redirect(url_for('user.profile'))

    return render_template('partials/_edit_vehicle.html', vehicle=vehicle)



@user_bp.route('/user/delete_vehicle/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id:
        abort(403)
    
    db.session.delete(vehicle)
    db.session.commit()
    flash('Vehicle deleted successfully', 'success')
    return redirect(url_for('user.profile'))



@user_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():

    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Your account has been permanently deleted', 'info')
    return redirect(url_for('user.user_signup'))