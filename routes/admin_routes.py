from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from functools import wraps
from datetime import datetime
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
    # Get all parking lots
    lots = ParkingLot.query.all()

    parking_lots = []

    for lot in lots:
        occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()

        parking_lots.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'number_of_spots': lot.number_of_spots,
            'occupied_spots': occupied_count,
        })

    return render_template('admin/dashboard.html', parking_lots=parking_lots)


@admin_bp.route('/users', methods=['GET', 'POST'])
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)



@admin_bp.route('/search', methods=['GET', 'POST'])
def admin_search():
    return render_template('admin/search.html')


@admin_bp.route('/activity_log', methods=['GET', 'POST'])
def activity_log():
    return render_template('admin/activity_log.html')



@admin_bp.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template('admin/statistics.html')



@admin_bp.route('/add_new_parking', methods=['GET', 'POST'])
def add_new_parking():
    return render_template('partials/_add_new_parking.html')



@admin_bp.route('/admin/add_parking_lot', methods=['POST'])
def add_parking_lot():
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        price_per_hour = float(request.form['price_per_hour'])
        number_of_spots = int(request.form['number_of_spots'])
        is_active = request.form['is_active'] == 'true'  
        
        available_from_str = request.form.get('available_from') 
        available_to_str = request.form.get('available_to')      

        available_from = datetime.strptime(available_from_str, "%H:%M").time()
        available_to = datetime.strptime(available_to_str, "%H:%M").time()

        # Create new ParkingLot object
        new_parking_lot = ParkingLot(
            prime_location_name=prime_location_name,
            address=address,
            pin_code=pin_code,
            price_per_hour=price_per_hour,
            number_of_spots=number_of_spots,
            available_from=available_from,
            available_to=available_to,
            is_active=is_active
        )

        # Add to database
        db.session.add(new_parking_lot)
        db.session.commit()

        return redirect(url_for('admin.admin_dashboard'))  # Redirect to admin dashboard


@admin_bp.route('/view_spot/<int:lot_id>/<int:spot_number>')
def view_spot(lot_id, spot_number):
    # logic to fetch and display info for that spot
    return f"Spot {spot_number} in lot {lot_id}"


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

    ParkingSpot.query.filter_by(lot_id=lot_id).delete()

    db.session.delete(parking_lot)
    db.session.commit()

    flash('Parking lot deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))



@admin_bp.route('/admin/flag_user_confirmation/', methods=['GET', 'POST'])
def flag_user_confirmation():
    return render_template('partials/_flag_user_confirmation.html')






