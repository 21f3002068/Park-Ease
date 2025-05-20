from model import *

def calculate_duration(start_time):
    now = datetime.now()  
    delta = now - start_time
    total_minutes = delta.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours}h {minutes}m"

def parse_time_string(time_str):
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Time data '{time_str}' is not in a recognized format")

def assign_pending_reservation(spot):
    now = datetime.now()
    matching_request = Reservation.query.filter(
        Reservation.spot_id.is_(None),  # Not yet assigned
        Reservation.status == 'Pending',
        Reservation.expected_arrival <= now,
        Reservation.expected_departure >= now,
        Reservation.lot_id == spot.lot_id  # Same lot
    ).order_by(Reservation.expected_arrival.asc()).first()

    if matching_request:
        matching_request.spot_id = spot.id
        matching_request.status = 'Confirmed'
        spot.status = 'B'  # Or 'O' if you're directly allowing parking
        db.session.commit()
