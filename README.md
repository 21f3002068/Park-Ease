# ParkEase - Smart Parking Management System
This is a Vehicle Parking web application specialized in four-wheelers. It is an academic project of Modern Application Development-1 under IITM BS Data Science and Applications offered by IIT Madras. 

## Overview
ParkEase is a comprehensive parking management solution designed to streamline parking operations for both administrators and users. The system provides real-time parking spot monitoring, reservation capabilities, and administrative controls for efficient parking lot management.

## Features
### Admin Features
Dashboard Overview: Visual representation of parking lot status
Spot Management: Add, edit, or disable parking spots
Real-time Monitoring: View current spot occupancy status
User Management: Administer user accounts and permissions
Summaries: View utilization reports and analytics

### User Features
Spot Reservation: Book available parking spots in advance
Real-time Availability: Check current parking availability
Bookmark Parking Lot: Save/Favorite frequently visited parking lot.
Vehicle Management: Store multiple vehicle profiles
History Tracking: View past parking sessions

## Technologies Used
### Frontend
HTML5, CSS3, JavaScript
Jinja2 templating
Werkzeug (security and password hashing)

### Backend
Python 3
Flask web framework
SQLAlchemy ORM
PostgreSQL (or SQLite for development)

## Additional Tools
ChartJs for statistical summaries for User/Admin Dashboards

## Setup
1. **Clone the repository**:  
   ```bash
    git clone https://github.com/yourusername/parkease.git
    cd parkease

2. **Set up a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt

4. **Configure the application**
   - Create a `.env` file based on `.env.example` and fill in your values:
   - ```bash
     cp .env.example .env
   - Set your database connection and secret key

5. **Run the development Server**
   ```bash
   python3 app.py

## Project Structure
  ```bash
    .
    ├── app.py
    ├── config.py
    ├── dummy_data.py
    ├── instance
    │   └── parkease.db
    ├── model.py
    ├── Project Report.pdf
    ├── README.md
    ├── requirements.txt
    ├── routes
    │   ├── admin_routes.py
    │   ├── __init__.py
    │   └── user_routes.py
    ├── static
    │   ├── icon
    │   ├── image
    │   ├── scripts
    │   ├── style
    │   └── uploads
    └── templates
        ├── admin
        ├── index.html
        ├── partials
        └── user


