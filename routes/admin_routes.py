from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import extract
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash


admin_bp= Blueprint('admin', __name__)

admin_username = "admin"
admin_password = "admin"

admin_password = generate_password_hash("admin")

def check_admin_credentials(username, password):
    return username == admin_username and check_password_hash(admin_password, password)

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



@admin_bp.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # Get the current date (today)
    today = datetime.today().date()

    # Count the number of reservations (vehicles parked) today
    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()

    # Get all parking lots and other info as before
    lots = ParkingLot.query.all()

    parking_lots = []

    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.number_of_spots or 1

        total_occupied_spots += occupied_count
        total_spots += total

        utilization = (occupied_count / total) * 100
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
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
        location_data.append({
            "location": loc,
            "lots": lots
        })
    
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.number_of_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
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
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.number_of_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()

    return render_template('admin/users.html', users=users,
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today)



@admin_bp.route('/search', methods=['GET', 'POST'])
def admin_search():
    return render_template('admin/search.html')


@admin_bp.route('/activity_log', methods=['GET', 'POST'])
def activity_log():
    users = User.query.all()
    today = datetime.today().date()
    lots = ParkingLot.query.all()

    vehicles_parked_today = Reservation.query.filter(Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())).count()
    parking_lots = []
    
    total_occupied_spots = 0
    total_spots = 0

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        total = lot.number_of_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
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
                           vehicles_parked_today=vehicles_parked_today)



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
        total = lot.number_of_spots or 1
        
        total_occupied_spots += occupied_count
        total_spots += total
        
        utilization = (occupied_count / total) * 100
        
        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
            'occupied_spots': occupied_count,
            'utilization_rate': round(utilization, 1)
        })

    hourly_occupancy = [0] * 24  # Initialize for 24 hours

    reservations_today = Reservation.query.filter(
        Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time())
    ).all()

    usage_trend = []
    date_labels = []

    for i in range(6, -1, -1):  # Last 7 days
        day = today - timedelta(days=i)
        count = Reservation.query.filter(
            Reservation.parking_timestamp >= datetime.combine(day, datetime.min.time()),
            Reservation.parking_timestamp <= datetime.combine(day, datetime.max.time())
        ).count()
        
        usage_trend.append(count)
        date_labels.append(day.strftime('%b %d'))
        
    for res in reservations_today:
        hour = res.parking_timestamp.hour
        hourly_occupancy[hour] += 1

    overall_utilization = round((total_occupied_spots / total_spots) * 100, 1) if total_spots else 0

    active_users = User.query.filter_by(is_active=True).count()
    total_parking_lots = ParkingLot.query.count()
    active_parkings = ParkingLot.query.filter_by(is_active=True).count()
    available_spots = total_spots - total_occupied_spots

    
    return render_template('admin/statistics.html',
                           active_users=active_users,
                           parking_lots=parking_lots, 
                           active_parkings=active_parkings, 
                           total_parking_lots=total_parking_lots,
                           utilization_rate=overall_utilization,
                           vehicles_parked_today=vehicles_parked_today,
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
        max_parking_spots = int(request.form['max_parking_spots'])

        new_location = Location(
            name=name,
            address=address,
            max_parking_spots=max_parking_spots
        )

        db.session.add(new_location)
        db.session.commit()

        flash('New location added successfully!', 'success')
        return redirect(url_for('admin.add_new_parking'))

    return render_template('partials/_add_new_location.html')





@admin_bp.route('/admin/add_parking_lot', methods=['POST'])
def add_parking_lot():
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        pin_code = request.form['pin_code']
        price_per_hour = float(request.form['price_per_hour'])
        number_of_spots = int(request.form['number_of_spots'])
        is_active = request.form['is_active'] == 'true'

        available_from_str = request.form.get('available_from')
        available_to_str = request.form.get('available_to')

        available_from = datetime.strptime(available_from_str, "%H:%M").time()
        available_to = datetime.strptime(available_to_str, "%H:%M").time()
        location_id = int(request.form['location_id'])

        # Create new ParkingLot object
        new_parking_lot = ParkingLot(
            prime_location_name=prime_location_name,
            pin_code=pin_code,
            price_per_hour=price_per_hour,
            number_of_spots=number_of_spots,
            available_from=available_from,
            available_to=available_to,
            is_active=is_active,
            location_id=location_id
        )

        # Commit to get new_parking_lot.id
        db.session.add(new_parking_lot)
        db.session.commit()

        # ✅ Create parking spots
        for i in range(new_parking_lot.number_of_spots):
            spot = ParkingSpot(lot_id=new_parking_lot.id, spot_number=i + 1)
            db.session.add(spot)
        db.session.commit()

        return redirect(url_for('admin.admin_dashboard'))


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

    # Decrement the number of spots in the parking lot
    if parking_lot.number_of_spots > 0:
        parking_lot.number_of_spots -= 1

    db.session.delete(spot)
    db.session.commit()

    flash("Spot deleted successfully.", "success")

    return redirect(url_for('admin.admin_dashboard'))  # Reload the parking lot page



def parse_time_string(time_str):
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Time data '{time_str}' is not in a recognized format")


@admin_bp.route('/admin/edit_parking/<int:lot_id>', methods=['GET', 'POST'])
def edit_parking(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        parking_lot.prime_location_name = request.form['prime_location_name']
        parking_lot.address = request.form['address']
        parking_lot.pin_code = request.form['pin_code']
        parking_lot.price_per_hour = float(request.form['price_per_hour'])
        parking_lot.number_of_spots = int(request.form['number_of_spots'])

        # Convert to datetime.time
        parking_lot.available_from = parse_time_string(request.form['available_from'])
        parking_lot.available_to = parse_time_string(request.form['available_to'])


        parking_lot.is_active = request.form['is_active'] == 'true'

        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('partials/_edit_parking.html', lot=parking_lot)



@admin_bp.route('/admin/delete_parking/<int:lot_id>', methods=['POST'])
def delete_parking(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    # Check if all parking spots are available
    has_occupied_spots = any(spot.status != 'A' for spot in parking_lot.spots)

    if has_occupied_spots:
        flash('Cannot delete parking lot. Some spots are still occupied.', 'error')
        return redirect(url_for('admin.admin_dashboard'))  # or wherever you want to redirect

    # If all spots are empty, proceed with deletion
    db.session.delete(parking_lot)
    db.session.commit()

    flash('Parking lot deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))




@admin_bp.route('/admin/flag_user_confirmation/', methods=['GET', 'POST'])
def flag_user_confirmation():
    return render_template('partials/_flag_user_confirmation.html')






