# ParkEase - Smart Parking Management System
This is a Vehicle Parking web application specialized in four-wheelers. It is an academic project of Modern Application Development-1 under IITM BS Data Science and Applications offered by IIT Madras. 

## Overview
ParkEase is a comprehensive parking management solution designed to streamline parking operations for both administrators and users. The system provides real-time parking spot monitoring, reservation capabilities, and administrative controls for efficient parking lot management.

## Features
### Admin Features
- **Dashboard Overview:** Visual representation of parking lot status
- **Spot Management:** Add, edit, or disable parking spots
- **Real-time Monitoring:** View current spot occupancy status
- **User Management:** Administer user accounts and permissions
- **Summaries:** View utilization reports and analytics

### User Features
- **Spot Reservation:** Book available parking spots in advance
- **Real-time Availability:** Check current parking availability
- **Bookmark Parking Lot:** Save/Favorite frequently visited parking lot.
- **Vehicle Management:** Store multiple vehicle profiles
- **History Tracking:** View past parking sessions

## Technologies Used
### Frontend
- HTML5, CSS3, JavaScript
- Jinja2 templating
- Werkzeug (security and password hashing)

### Backend
- Python 3
- Flask web framework
- SQLAlchemy ORM
- PostgreSQL (or SQLite for development)

### Additional Tools
- ChartJs for statistical summaries for User/Admin Dashboards

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
       ```bash
     cp .env.example .env
   - Set your database connection and secret key

5. **Run the development Server**
   ```bash
   python3 app.py

5. Project Structure
   ```bash
   park_ease_21f3002068
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


## Screenshots
### Admin Dashboard
![image](https://github.com/user-attachments/assets/d2df24e1-5d4a-483e-b8b9-f366148e3230)
![image](https://github.com/user-attachments/assets/03a74c75-f008-4d1a-a8ef-f965aa169cda)
![image](https://github.com/user-attachments/assets/33fb7a92-c51e-4c94-83e4-6c67bfa6d1e0)
![image](https://github.com/user-attachments/assets/54561816-74c5-4779-96b4-df70ace21678)
![image](https://github.com/user-attachments/assets/e14b3341-6fda-4587-b98a-87ed5f7b78f7)


### User Dashboard
![image](https://github.com/user-attachments/assets/4e661102-28ff-4666-85e9-852a22d67c73)
![image](https://github.com/user-attachments/assets/e646f5f0-b561-447a-a1e7-f9e717f5b0ca)
![image](https://github.com/user-attachments/assets/8f786e54-514b-4635-ab50-ee0129bdae68)
![image](https://github.com/user-attachments/assets/971284a1-3777-4ed2-8410-451f67618b3e)
![image](https://github.com/user-attachments/assets/dbe790cd-ebc1-467f-8f49-61e9be44c220)



## Contact
For questions and support, please contact:
- Project Maintainer: **Vaibhav Satish**
- Email: 21f3002068@ds.study.iitm.ac.in


