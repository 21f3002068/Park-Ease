from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # Core Credentials
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Extra Profile Info
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin = db.Column(db.String(10), nullable=False)

    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    max_parking_spots = db.Column(db.Integer, nullable=False)
    
    # Define parking_lots relationship
    parking_lots = db.relationship('ParkingLot', backref='location_ref', lazy=True)
    
    def __repr__(self):
        return f'<Location {self.name}>'



class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    price_per_hour = db.Column(db.Float)
    number_of_spots = db.Column(db.Integer, nullable=False)
    available_from = db.Column(db.Time)
    available_to = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign key to Location
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
        
    # Not using these rn
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String)
    admin_notes = db.Column(db.Text)
    # In ParkingLot model
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete-orphan', lazy=True)

    
    def __repr__(self):
        return f'<ParkingLot {self.prime_location_name}>'


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied



class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))

    parking_timestamp = db.Column(db.DateTime)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancellation_reason = db.Column(db.String(200))
    
    # Define relationships - removed backref from vehicle
    spot = db.relationship('ParkingSpot', backref='reservations')
    user = db.relationship('User', backref='reservations')
    vehicle = db.relationship('Vehicle')  # No backref here

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_name = db.Column(db.String(100))
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    color = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship - using back_populates instead of backref
    reservations = db.relationship('Reservation', back_populates='vehicle', lazy=True)

    def __repr__(self):
        return f'<Vehicle {self.license_plate}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservation = db.relationship('Reservation', backref=db.backref('review', uselist=False))