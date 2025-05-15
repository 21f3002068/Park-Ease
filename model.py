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
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    pin = db.Column(db.String(10))

    registration_date = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    reservations = db.relationship('Reservation', backref='user_ref', lazy=True)
    vehicles = db.relationship('Vehicle', backref='owner', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_flagged(self):
        latest_flag = sorted(self.flags, key=lambda f: f.flag_date, reverse=True)
        return latest_flag[0].is_flagged if latest_flag else False



class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10))
    
    # Define parking_lots relationship
    parking_lots = db.relationship('ParkingLot', backref='location_ref', lazy=True)
    
    def __repr__(self):
        return f'<Location {self.name}>'



class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100))
    price_per_hour = db.Column(db.Float)
    
    max_parking_spots = db.Column(db.Integer, nullable=False)
    available_spots = db.Column(db.Integer, nullable=False)
    
    available_from = db.Column(db.Time)
    available_to = db.Column(db.Time)
    
    is_active = db.Column(db.Boolean, default=True)
    
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
        
    # Not using these as of now
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String)
    admin_notes = db.Column(db.Text)
    # In ParkingLot model
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete-orphan', lazy=True)

    
    def __repr__(self):
        return f'<ParkingLot {self.prime_location_name}>'

    def get_available_spots(self, when=None):
        when = when or datetime.now()
        return sum(
            1 for spot in self.spots
            if spot.status == 'A' and not spot.has_conflicting_reservation(when)
        )


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied

    def has_conflicting_reservation(self, when):
        return bool(Reservation.query.filter(
            Reservation.spot_id == self.id,
            Reservation.status == 'Confirmed',
            Reservation.expected_arrival <= when,
            Reservation.expected_departure >= when
        ).first())

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(50), unique=True, nullable=False)
    booking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))

    expected_arrival = db.Column(db.DateTime, nullable=False)
    expected_departure = db.Column(db.DateTime, nullable=False)

    parking_timestamp = db.Column(db.DateTime)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancellation_reason = db.Column(db.String(200))

    lot = db.relationship('ParkingLot')
    spot = db.relationship('ParkingSpot', backref=db.backref('reservations', lazy='dynamic'))
    user = db.relationship('User')
    vehicle = db.relationship('Vehicle')



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


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  

    user = db.relationship('User', backref='favorites')
    lot = db.relationship('ParkingLot', backref='favorites')



class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservation = db.relationship('Reservation', backref=db.backref('review', uselist=False))
    
    
    
class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(200))
    flag_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='flags')
