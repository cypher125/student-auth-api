# Yabatech Facial Recognition System Setup Guide

This guide provides step-by-step instructions for setting up the Yabatech Facial Recognition System on your local development environment and deploying it to production using Render.

## Prerequisites

Before you start, ensure you have the following installed:

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Virtual environment tool (virtualenv or venv)

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/yabatech-facial-recognition.git
cd yabatech-facial-recognition
```

### 2. Create and Activate Virtual Environment

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration values:

```
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# JWT settings
ACCESS_TOKEN_LIFETIME_MINUTES=15
REFRESH_TOKEN_LIFETIME_DAYS=7

# CORS settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Face recognition settings
FACE_RECOGNITION_MODEL=VGG-Face
FACE_RECOGNITION_THRESHOLD=0.6
```

### 5. Set Up the Database

```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 7. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at http://localhost:8000/api/

## Setting Up Facial Recognition

The system uses InsightFace for face recognition, which requires specific dependencies:

### 1. Install Required System Packages

#### For Windows:

Ensure you have Visual C++ build tools installed.

#### For Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx
```

#### For macOS:

```bash
brew install opencv
```

### 2. Verify Face Recognition Dependencies

The face recognition dependencies are installed as part of the requirements.txt file.
Ensure the following packages are installed:

- insightface
- onnxruntime
- opencv-python
- numpy
- mtcnn

### 3. Test Face Recognition

You can test the face recognition system by:

1. Creating a student account via the admin panel
2. Registering a face through the API
3. Testing recognition with a sample image

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Production Deployment on Render

### 1. Prepare for Render Deployment

#### Create Required Files

1. Create a `build.sh` file in the project root:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

2. Create a `render.yaml` file (optional, for Blueprint deployment):

```yaml
services:
  - type: web
    name: yabatech-facial-recognition
    env: python
    buildCommand: ./build.sh
    startCommand: gunicorn facial_recognition_api.wsgi:application
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: yabatech-facial-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: ".onrender.com,your-custom-domain.com"
      - key: FACE_RECOGNITION_MODEL
        value: "VGG-Face"
      - key: FACE_RECOGNITION_THRESHOLD
        value: "0.6"

databases:
  - name: yabatech-facial-db
    databaseName: yabatech_facial_recognition
    plan: starter
```

3. Add a `runtime.txt` file to specify the Python version:

```
python-3.11.8
```

4. Make sure your `requirements.txt` includes:

```
gunicorn
whitenoise
psycopg2-binary
dj-database-url
```

5. Update your `settings.py` to support Render's PostgreSQL and environment variables:

```python
# Add these imports
import os
import dj_database_url
from pathlib import Path

# Update database configuration
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# Configure static files for Render
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add whitenoise middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ...other middleware...
]
```

### 2. Deploy to Render

#### Option 1: Manual Deployment

1. Sign up or log in to [Render](https://render.com/)

2. From the dashboard, click "New +" and select "Web Service"

3. Connect your GitHub repository or use the public repository URL

4. Configure your web service:
   - **Name**: yabatech-facial-recognition
   - **Environment**: Python
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn facial_recognition_api.wsgi:application`
   - **Plan**: Select an appropriate plan (Free for testing)

5. Add environment variables:
   - `SECRET_KEY` - Generate a secure random key
   - `DEBUG` - Set to "False"
   - `ALLOWED_HOSTS` - Add your Render URL and any custom domains
   - `FACE_RECOGNITION_MODEL` - "VGG-Face"
   - `FACE_RECOGNITION_THRESHOLD` - "0.6"

#### Option 2: Using Render Blueprint (render.yaml)

1. Push your `render.yaml` file to your GitHub repository

2. In Render dashboard, click "New +" and select "Blueprint"

3. Connect your GitHub repository

4. Render will automatically set up the services defined in your `render.yaml` file

### 3. Set Up PostgreSQL Database

1. From the Render dashboard, click "New +" and select "PostgreSQL"

2. Configure your database:
   - **Name**: yabatech-facial-db
   - **Database**: yabatech_facial_recognition
   - **User**: Render will generate automatically
   - **Plan**: Select appropriate plan (Free for testing)

3. Once created, copy the "Internal Database URL" from the database dashboard

4. Add the database URL as an environment variable in your web service:
   - `DATABASE_URL` - Paste the copied internal database URL

### 4. Custom Domain (Optional)

1. In your web service dashboard, go to the "Settings" tab

2. Under "Custom Domain", click "Add Domain"

3. Enter your domain name and follow the instructions to configure DNS settings

### 5. Monitoring and Scaling

1. Monitor your application's performance on the Render dashboard

2. View logs by clicking on your web service and selecting the "Logs" tab

3. Scale up your application by upgrading your plan if needed

## Common Issues and Troubleshooting

### Deployment Issues

- **Build failures**: Check build logs for details and ensure all dependencies are correctly specified
- **Runtime errors**: Check application logs in Render dashboard
- **Database connection issues**: Verify the `DATABASE_URL` environment variable is set correctly

### Face Recognition Issues

- **No face detected**: Ensure the image has a clear, well-lit face
- **Recognition accuracy low**: Adjust the FACE_RECOGNITION_THRESHOLD value in environment variables
- **InsightFace dependency errors**: Render may need specific buildpacks for OpenCV support

## Maintenance

### Database Backups

Render automatically performs daily backups of your PostgreSQL database on paid plans. You can also:

1. Go to your database in the Render dashboard
2. Click on "Backups" tab
3. Click "Manual Backup" to create a backup
4. Download backups for local storage

### Updates and Continuous Deployment

1. Configure automatic deployments from your repository:
   - In your web service dashboard, go to "Settings"
   - Under "Deploy Hooks", configure auto-deployment on specific branches

2. Make changes to your repository:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

3. Render will automatically deploy the new version if auto-deploy is enabled

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django on Render Guide](https://render.com/docs/deploy-django)
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [InsightFace Documentation](https://github.com/deepinsight/insightface) 