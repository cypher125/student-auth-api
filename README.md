# Yabatech Facial Recognition System

A facial recognition authentication and management system built for Yabatech, leveraging deep learning to provide secure, contactless student identification and attendance tracking.

![Yabatech Facial Recognition](https://via.placeholder.com/800x400?text=Yabatech+Facial+Recognition+System)

## Features

- **Facial Recognition Authentication**: Secure login using facial biometrics
- **Student Management**: Complete student record management system
- **Admin Dashboard**: Analytics and system monitoring
- **Recognition Logs**: Comprehensive audit trail of recognition attempts
- **RESTful API**: Well-documented API for integration with other systems
- **Role-based Access Control**: Different permissions for students and administrators
- **JWT Authentication**: Secure token-based authentication

## Technology Stack

- **Backend**: Django, Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT (JSON Web Token)
- **Face Recognition**: InsightFace, OpenCV, MTCNN
- **Documentation**: Swagger/OpenAPI, ReDoc

## System Requirements

- Python 3.11+
- Django 5.1+
- InsightFace and its dependencies
- Docker (optional, for containerized deployment)

## Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/yabatech-facial-recognition.git
   cd yabatech-facial-recognition
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the API at http://localhost:8000/api/

### API Documentation

- Swagger UI: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- ReDoc: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

## Documentation

We have comprehensive documentation for all aspects of the system:

- [Setup Guide](setup_guide.md) - Installation and configuration instructions
- [API Documentation](api_documentation.md) - Detailed API endpoints reference
- [Database Schema](database.md) - Database structure and relationships
- [Architecture Overview](architecture_overview.md) - System design and components

## Key Components

### User Management

The system supports two main user types:
- **Students**: Users who authenticate with facial recognition
- **Admins**: Users who manage students and system settings

### Facial Recognition

The facial recognition pipeline includes:
1. Face detection using MTCNN
2. Feature extraction using InsightFace
3. Face comparison with stored templates
4. Confidence score calculation and threshold-based matching

### Authentication Flow

1. User uploads their face image via the API
2. System detects and processes the face
3. Face is compared against registered students
4. If matched, JWT tokens are issued for authentication
5. The recognition attempt is logged for audit purposes

## Screenshots

![Dashboard](https://via.placeholder.com/800x400?text=Dashboard)
![Recognition](https://via.placeholder.com/800x400?text=Face+Recognition)
![Student Management](https://via.placeholder.com/800x400?text=Student+Management)

## Contributing

We welcome contributions to the Yabatech Facial Recognition System! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Project Team - [admin@yabatech.edu.ng](mailto:osawayecyrus@gmail.com)

Project Link: [https://github.com/cypher125/StudentAuth](https://github.com/cypher125/StudentAuth)

## Acknowledgements

- [InsightFace](https://github.com/deepinsight/insightface) - Face recognition technology
- [Django REST Framework](https://www.django-rest-framework.org/) - API framework
- [SimpleJWT](https://github.com/jazzband/djangorestframework-simplejwt) - JWT authentication
