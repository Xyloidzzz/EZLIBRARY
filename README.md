# EZLIBRARY - Library Management System

## Overview

EZLIBRARY (Bookworms) is a comprehensive library management system built with Flask, designed to help libraries efficiently manage their resources and services.

## Features

- Book Management
- User Management
- Room Reservation System
- Equipment Checkout
- Fine Tracking and Management

## Technology Stack

- **Backend**: Python/Flask
- **Frontend**: HTML/CSS
- **Database**: MySQL and AWS

## Project Structure

```
EZLIBRARY/
├── static/
│   └── styles/
│       └── styles.css
├── templates/
│   └── Home.html
├── bookworms.py
└── README.md
```

## Setup and Installation

1. Clone the repository

2. Install required dependencies:

   ```bash
   pip install flask
   ```

<!-- 3. Set up the database (MySQL) and configure the connection in `bookworms.py`. -->

## Running the Application

To run the application locally:

```bash
flask --app bookworms run
```

Access the application at `http://localhost:5000`

## Development Status

- [x] Basic project structure
- [x] Initial Flask setup
- [x] Basic frontend template
- [ ] Database implementation
- [ ] User authentication
- [ ] Book management features
- [ ] Room reservation system
- [ ] Equipment checkout system
- [ ] Fine management system
