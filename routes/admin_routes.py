from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
from datetime import datetime
import os
from flask import current_app

admin_bp= Blueprint('admin', __name__)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin"))

def check_admin_credentials(username, password):
    return username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_admin_credentials(username, password):
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin/admin_login.html')



@admin_bp.route('/dashboard/search', methods=['GET'])
def admin_search():
    query = request.args.get('query')

    # Convert the query to lowercase to make the search case-insensitive
    query_lower = query.lower()
    
    locations = Location.query.all()
    location_count = Location.query.count()
    
    total_users = User.query.count()
    

    reservation_count = Reservation.query.count()
    reservations = Reservation.query.all()
    
    pending_bookings = Reservation.query.filter_by(status='Pending').count()
    confirmed_bookings = Reservation.query.filter_by(status='Confirmed').count()
    cancelled_rejected_bookings = Reservation.query.filter(
        or_(Reservation.status == 'Reject', Reservation.status == 'Cancelled')
    ).count()    
    parked_out = Reservation.query.filter_by(status='Parked Out').count()

    results = {
        'users': User.query.filter(
            (User.firstname.ilike(f'%{query}%')) |
            (User.lastname.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%')) |
            (User.username.ilike(f'%{query}%')) |
            (User.phone.ilike(f'%{query}%'))
        ).all(),

        'location': Location.query.filter(
            (Location.name.ilike(f'%{query}%')) |
            (Location.address.ilike(f'%{query}%'))    
        ).all(),

        'parkinglot': ParkingLot.query.filter(
            (ParkingLot.prime_location_name.ilike(f'%{query}%')) 
        ).all(),

        'reservations': Reservation.query.filter(
            (Reservation.id == query) |
            (Reservation.status.ilike(f'%{query}%'))
        ).all(),
    }

    # Flatten the results and include more context
    flat_results = []
    for entity, items in results.items():
        for item in items:
            flat_results.append({
                'entity': entity,
                'result': item
            })

    return render_template('admin/search.html',
                           results=flat_results,
                           query=query,
                           locations=locations,
                           location_count=location_count,
                           total_users=total_users,
                           reservations=reservations,
                           reservation_count=reservation_count,
                           pending_bookings=pending_bookings,
                           confirmed_bookings=confirmed_bookings,
                           cancelled_rejected_bookings=cancelled_rejected_bookings,
                           parked_out=parked_out)




@admin_bp.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Get the current date (today)
    today = datetime.today().date()

    # Count the number of reservations (vehicles parked) today
    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()

    # Get all parking lots and other info as before
    lots = ParkingLot.query.order_by(ParkingLot.is_active.desc()).all()

    parking_lots = []

    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()

        total = lot.available_spots or 1

        total_occupied_spots += occupied_count
        total_spots += total

        utilization = (occupied_count / total) * 100
        parking_lots.append({
            'id': lot.id,
            'spots': spots,
            'prime_location_name': lot.prime_location_name,
            'available_spots': lot.available_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()

    return render_template('admin/dashboard.html', 
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today)
    
    
    
@admin_bp.route('/parking_locations', methods=['GET', 'POST'])
def locations():
    
    all_locations = Location.query.all()
    location_data = []

    for loc in all_locations:
        lots = ParkingLot.query.filter_by(location_id=loc.id).all()
        
        # Calculate total available spots for the current location
        total_available_spots = 0
        for lot in lots:
            # Get count of available spots in each lot
            available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
            total_available_spots += available_spots
        
        location_data.append({
            "location": loc,
            "lots": lots,
            "total_available_spots": total_available_spots  # Add the total available spots
        })
    
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.available_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'available_spots': lot.available_spots,
            'max_parking_spots': lot.max_parking_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()
    
    selected_location_id = request.args.get('location_id', type=int)
    selected_location = Location.query.get(selected_location_id) if selected_location_id else None

    return render_template('admin/locations.html',
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today,
                           location_data=location_data,
                           selected_location_id=selected_location_id,
                           selected_location=selected_location)





@admin_bp.route('/users', methods=['GET', 'POST'])
def admin_users():
    users = User.query.all()
    user_ids = [user.id for user in users]
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    formatted_dates = [user.registration_date.strftime('%b %d') for user in users if user.registration_date]
    booking_counts = [len(user.reservations) for user in users]

    # Count registrations by date
    date_counts = Counter(formatted_dates)
    labels = list(date_counts.keys())
    counts = list(date_counts.values())

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.available_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'available_spots': lot.available_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()

    return render_template('admin/users.html',
                           users=users,
                           active_users=active_users,
                           parking_lots=parking_lots,
                           active_parkings=active_parkings,
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today,
                           labels=labels,  
                           counts=counts,
                           user_ids=user_ids,
                           booking_counts=booking_counts)  


@admin_bp.route('/users/view_user/<int:user_id>')
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    user.reservations = Reservation.query.filter_by(user_id=user_id).all()
    return render_template('partials/_view_user_details.html', user=user)



@admin_bp.route('/activity_log', methods=['GET', 'POST'])
def activity_log():
    users = User.query.all()
    today = datetime.today().date()
    lots = ParkingLot.query.all()
    reservations = Reservation.query.order_by(Reservation.booking_timestamp.desc()).all()
    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.available_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'available_spots': lot.available_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()
    return render_template('admin/activity_log.html',
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today,
                           reservations=reservations)


@admin_bp.route('/reservations/booking_details/<string:booking_id>', methods=['GET', 'POST'])
def booking_details(booking_id):
    reservation = Reservation.query.filter_by(booking_id=booking_id).first()

    if reservation:

        return render_template('partials/_admin_views_booking_details.html', reservation=reservation)
    else:

        flash('Booking not found', 'error')
        return redirect(url_for('user.bookings')) 



@admin_bp.route('/statistics', methods=['GET', 'POST'])
def statistics():
    
    users = User.query.all()
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.available_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'available_spots': lot.available_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    hourly_occupancy = [0] * 24
    all_reservations = Reservation.query.all()  # Get ALL reservations, not just today's

    for res in all_reservations:
        if res.expected_arrival:  # Ensure the field exists
            hour = res.expected_arrival.hour
            hourly_occupancy[hour] += 1

    total_reservations = max(1, sum(hourly_occupancy))  # Avoid division by zero
    hourly_occupancy = [round((count / total_reservations * 100),2) for count in hourly_occupancy]
    
    usage_trend = []
    date_labels = []

    for i in range(6, -1, -1):  # Last 7 days
        day = today - timedelta(days=i)
        count = Reservation.query.filter(
            Reservation.expected_arrival >= datetime.combine(day, datetime.min.time()),
            Reservation.expected_arrival <= datetime.combine(day, datetime.max.time())
        ).count()
        
        usage_trend.append(count)
        date_labels.append(day.strftime('%b %d'))
        

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()
    available_spots = total_spots - total_occupied_spots

    duration_brackets = [0] * 5  # [<1h, 1-2h, 2-4h, 4-8h, 8+h]
    completed_reservations = Reservation.query.filter(
        Reservation.expected_arrival >= datetime.combine(today - timedelta(days=7), datetime.min.time()),
        Reservation.leaving_timestamp.isnot(None)
    ).all()

    # Count raw values first
    for res in completed_reservations:
        duration_hours = round(((res.leaving_timestamp - res.parking_timestamp).total_seconds() / 3600), 2)
        
        if duration_hours < 1:
            duration_brackets[0] += 1
        elif 1 <= duration_hours < 2:
            duration_brackets[1] += 1
        elif 2 <= duration_hours < 4:
            duration_brackets[2] += 1
        elif 4 <= duration_hours < 8:
            duration_brackets[3] += 1
        else:
            duration_brackets[4] += 1

    # Convert to percentages
    total_reservations = max(1, sum(duration_brackets))  # Avoid division by zero
    duration_percentages = [round((count / total_reservations * 100), 1) for count in duration_brackets]

    pending_count = Reservation.query.filter_by(status='Pending').count()
    parked_count = Reservation.query.filter_by(status='Parked').count()
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
        'parked': parked_count,
        'confirmed': confirmed_count,
        'parked_out': parked_out_count,
        'cancelled_rejected': combined_count
        
    }



    return render_template('admin/statistics.html',
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today,
                           status_data=status_data,
                           parking_durations=duration_percentages,
                           

                           occupied_spots=total_occupied_spots,
                           available_spots=available_spots,
                           hourly_occupancy=hourly_occupancy,
                           usage_trend=usage_trend,
                           date_labels=date_labels,
)



@admin_bp.route('/add_new_parking', methods=['GET', 'POST'])
def add_new_parking():
    locations = Location.query.all()
    if not locations:
        flash("Please add a location before creating a parking lot.", "warning")
        return redirect(url_for('admin.add_location'))

    selected_location_id = request.args.get('location_id', type=int)
    return render_template(
        'partials/_add_new_parking.html',
        locations=locations,
        selected_location_id=selected_location_id
    )



@admin_bp.route('/location/add_new_location', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        pin_code = int(request.form['pin_code'])

        new_location = Location(
            name=name,
            address=address,
            pin_code=pin_code
        )

        db.session.add(new_location)
        db.session.commit()

        flash('New location added successfully!', 'success')
        return redirect(url_for('admin.add_new_parking'))

    return render_template('partials/_add_new_location.html')



from utils import *

@admin_bp.route('/admin/add_parking_lot', methods=['POST'])
def add_parking_lot():
    file = request.files.get('image_url')
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(request.url)

    # Change parking lot upload to:
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'parking_lots')
        os.makedirs(upload_dir, exist_ok=True)  # Ensure directory exists
        file.save(os.path.join(upload_dir, filename))  # Save to subfolder
        image_url = f'uploads/parking_lots/{filename}'  

    try:
        prime_location_name = request.form.get('prime_location_name', '')
        price_per_hour = float(request.form.get('price_per_hour', 0))
        available_spots = int(request.form.get('available_spots', 0))
        max_parking_spots = int(request.form.get('max_parking_spots', 0))
        is_active = request.form.get('is_active') == 'true'

        if available_spots > max_parking_spots:
            flash('Available spots cannot exceed maximum spots.')
            return redirect(request.url)

        available_from = datetime.strptime(request.form.get('available_from', '00:00'), "%H:%M").time()
        available_to = datetime.strptime(request.form.get('available_to', '23:59'), "%H:%M").time()
        location_id = int(request.form.get('location_id', 0))
        admin_notes = request.form.get('admin_notes', '')

        new_parking_lot = ParkingLot(
            prime_location_name=prime_location_name,
            price_per_hour=price_per_hour,
            available_spots=available_spots,
            max_parking_spots=max_parking_spots,
            available_from=available_from,
            available_to=available_to,
            is_active=is_active,
            location_id=location_id,
            image_url=image_url,
            admin_notes=admin_notes
        )

        db.session.add(new_parking_lot)
        db.session.commit()

        # Create parking spots
        for i in range(available_spots):
            db.session.add(ParkingSpot(lot_id=new_parking_lot.id, spot_number=i + 1))
        db.session.commit()

        flash('Parking lot added successfully.')
        return redirect(url_for('admin.admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}")
        return redirect(request.url)


@admin_bp.route('/view_spot/<int:lot_id>/<int:spot_number>')
def view_spot(lot_id, spot_number):
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, spot_number=spot_number).first_or_404()
    
    if spot.status == 'O':
        reservation = Reservation.query.filter_by(spot_id=spot.id).order_by(Reservation.parking_timestamp.desc()).first()
        vehicle = reservation.vehicle if reservation else None
        user = User.query.get(reservation.user_id) if reservation else None

        return render_template('partials/_parking_spot_details.html',
                               spot=spot, reservation=reservation,
                               vehicle=vehicle, user=user)
    elif spot.status == 'B':
        reservation = Reservation.query.filter_by(spot_id=spot.id).order_by(Reservation.expected_arrival.desc()).first()
        vehicle = reservation.vehicle if reservation else None
        user = User.query.get(reservation.user_id) if reservation else None
        
        return render_template('partials/_parking_spot_details.html',
                               spot=spot, reservation=reservation,
                               vehicle=vehicle, user=user)
    
    else:
        return render_template('partials/_parking_spot_details.html',
                               spot=spot, reservation=None,
                               vehicle=None, user=None)


@admin_bp.route('/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    # Ensure the spot is not occupied
    if spot.status == 'O':
        flash("Cannot delete an occupied spot.", "warning")
        return redirect(request.referrer)

    # Get the corresponding parking lot
    parking_lot = ParkingLot.query.get(spot.lot_id)

    # Mark the spot as unavailable (soft delete)
    spot.status = 'X'

    # Decrement the number of available spots
    if parking_lot.available_spots > 0:
        parking_lot.available_spots -= 1

    db.session.commit()

    flash("Spot marked as unavailable (soft deleted).", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/restore_spot/<int:spot_id>', methods=['POST'])
def restore_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    if spot.status != 'X':
        flash("Spot is already active or occupied.", "info")
        return redirect(request.referrer)

    # Restore the spot
    spot.status = 'A'

    # Increment available spots in the corresponding lot
    parking_lot = ParkingLot.query.get(spot.lot_id)
    parking_lot.available_spots += 1

    db.session.commit()

    flash("Spot has been restored and is now available.", "success")
    return redirect(url_for('admin.admin_dashboard'))





@admin_bp.route('/admin/edit_parking/<int:lot_id>', methods=['GET', 'POST'])
def edit_parking(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    
    # Handle file upload only if new file was provided
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '' and allowed_file(file.filename):
            # Delete old image if exists
            if parking_lot.image_url:
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], parking_lot.image_url)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Save new image
            filename = secure_filename(file.filename)
            unique_name = f"lot_{lot_id}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'parking_lots', unique_name)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)
            parking_lot.image_url = f"uploads/parking_lots/{unique_name}"
    
    

    if request.method == 'POST':
        # Check if admin is trying to mark the lot inactive
        new_active_state = request.form['is_active'] == 'true'
        
        if not new_active_state and parking_lot.is_active:
            # Count active bookings or parked vehicles
            active_reservations = Reservation.query.join(ParkingSpot).filter(
                ParkingSpot.lot_id == lot_id,
                Reservation.status.in_(['Confirmed', 'Pending', 'Parked'])
            ).count()

            if active_reservations > 0:
                flash(f"Cannot deactivate this lot. There are {active_reservations} active or upcoming bookings exist.", "danger")
                return redirect(url_for('admin.edit_parking', lot_id=lot_id))


        new_from = parse_time_string(request.form['available_from'])
        new_to = parse_time_string(request.form['available_to'])

        # Find future bookings outside new time range


        relevant_bookings = Reservation.query.join(ParkingSpot).filter(
            ParkingSpot.lot_id == lot_id,
            or_(
                Reservation.status.in_(['Confirmed', 'Pending']) & (Reservation.expected_arrival > datetime.now()),
                Reservation.status == 'Parked'
            )
        ).all()

        # Identify those that would be affected by new time range
        affected_bookings = [
            b for b in relevant_bookings
            if b.expected_arrival.time() < new_from or b.expected_arrival.time() > new_to or b.expected_departure.time() > new_to
        ]

        if affected_bookings:
            # Calculate dynamic suggestion from full relevant set
            min_time = min(b.expected_arrival.time() for b in relevant_bookings)
            max_time = max(b.expected_departure.time() for b in relevant_bookings)

            suggested_from = min_time.strftime('%H:%M')
            suggested_to = max_time.strftime('%H:%M')


        
        if affected_bookings:
            flash('⚠️ Some future bookings fall outside the new available time range.', 'warning')
            return render_template(
                'partials/_edit_parking.html',
                lot=parking_lot,
                affected_bookings=affected_bookings,
                suggested_from=suggested_from,
                suggested_to=suggested_to
            )

        existing_spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_number).all()
        existing_count = len(existing_spots)
        new_count = int(request.form['available_spots'])

        if new_count > existing_count:
            # Add new spots
            for i in range(existing_count + 1, new_count + 1):
                new_spot = ParkingSpot(
                    lot_id=lot_id,
                    spot_number=i,
                    status='A'  
                )
                db.session.add(new_spot)
        elif new_count < existing_count:
            # Remove only unoccupied/unbooked/unreserved spots from the end
            removable = [s for s in reversed(existing_spots) if s.status not in ['O', 'B', 'X']]
            to_remove = removable[:existing_count - new_count]
            
            if len(to_remove) < (existing_count - new_count):
                flash("⚠️ Cannot remove that many spots because some are in use or booked.", "warning")
                return redirect(url_for('admin.edit_parking', lot_id=lot_id))

            for spot in to_remove:
                db.session.delete(spot)

        # Proceed with update
        parking_lot.prime_location_name = request.form['prime_location_name']
        parking_lot.price_per_hour = float(request.form['price_per_hour'])
        parking_lot.available_spots = new_count
        parking_lot.available_from = new_from
        parking_lot.available_to = new_to
        parking_lot.is_active = new_active_state

        db.session.commit()
        flash("Parking lot updated successfully.", "success")
        return redirect(url_for('admin.admin_dashboard'))


    return render_template('partials/_edit_parking.html', lot=parking_lot)



@admin_bp.route('/admin/delete_parking/<int:lot_id>', methods=['POST'])
def delete_parking(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    # Check if all parking spots are available
    has_occupied_spots = any(spot.status != 'A' for spot in parking_lot.spots)

    if has_occupied_spots:
        flash('Cannot delete parking lot. Some spots are still occupied or booked.', 'error')
        return redirect(url_for('admin.admin_dashboard'))  

    # If all spots are empty, proceed with deletion
    db.session.delete(parking_lot)
    db.session.commit()

    flash('Parking lot deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))



@admin_bp.route('/admin/flag_user_confirmation/<int:id>', methods=['GET', 'POST'])
def flag_user_confirmation(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        reason = request.form['reason']
        
        # Always create new flag
        flag = Flag(
            user_id=user.id,
            reason=reason,
            flag_date=datetime.now(),
            is_flagged=True
        )
        db.session.add(flag)
        db.session.commit()
        
        user.is_active = False
        db.session.commit()
        
        flash('User flagged successfully!', 'success')
        
        return redirect(url_for('admin.flagged_users'))

    return render_template('partials/_flag_user_confirmation.html', user=user)


@admin_bp.route('/admin/users/flagged')
def flagged_users():
    flagged_users = Flag.query.all()
    return render_template('admin/flagged_users.html', flagged_users=flagged_users)


@admin_bp.route('/admin/unflag_user/<int:id>', methods=['POST'])
def unflag_user(id):
    user = User.query.get_or_404(id)
    flag = Flag.query.filter_by(user_id=user.id).first() 

    if flag:
        db.session.delete(flag)  # Delete the flag
        db.session.commit()

    user.is_active = True  # Set the user back to active
    db.session.commit()

    return redirect(url_for('admin.flagged_users'))


@admin_bp.route('/admin/user_stats')
def user_stats():
    users = User.query.all()

    # User registration stats
    formatted_dates = [user.registration_date.strftime('%b %d') for user in users]
    date_counts = Counter(formatted_dates)
    labels = list(date_counts.keys())
    counts = list(date_counts.values())

    # Bookings per user
    user_ids = [user.id for user in users]
    booking_counts = [len(user.reservations) for user in users]  # Assuming User has a backref 'reservations'

    return render_template(
        'admin/users.html',
        users=users,
        labels=labels,
        counts=counts,
        user_ids=user_ids,
        booking_counts=booking_counts
    )

@admin_bp.route('/admin/users/delete/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id) 

    if user.is_flagged:
        flash("Flagged users must be reviewed before deletion.", "warning")
        return redirect(url_for('admin.admin_users'))

    try:
        db.session.delete(user)  
        db.session.commit()  
        flash('User has been deleted successfully!', 'success')  
    except Exception as e:
        db.session.rollback()  
        flash(f'Error deleting user: {str(e)}', 'danger')

    return redirect(url_for('admin.admin_users'))  
