# Yabatech Facial Recognition System API Documentation

This document provides detailed information about the Yabatech Facial Recognition System API endpoints, request/response formats, and authentication requirements.

## API Base URL

Development: `http://localhost:8000/api/`
Production: `https://your-production-domain.com/api/`

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints:

1. Obtain JWT tokens by calling the login endpoint or using facial recognition
2. Include the access token in the Authorization header as a Bearer token:
   ```
   Authorization: Bearer <access_token>
   ```
3. When the access token expires, use the refresh token to obtain a new one

### Token Endpoints

#### Login

```
POST /users/login/
```

Authenticates a user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "role": "student",
    "first_name": "John",
    "last_name": "Doe",
    "matric_number": "ABC123",
    "department": "Computer Science"
  }
}
```

#### Token Refresh

```
POST /users/token/refresh/
```

Obtains a new access token using a refresh token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

## User Management

### List All Users

```
GET /api/all-users/
```

Returns a list of all users in the system (requires admin permissions).

**Response:**
```json
[
  {
    "id": "uuid-string",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "role": "student",
    "faculty": "Engineering",
    "department": "Computer Science"
  },
  {
    "id": "uuid-string",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "role": "admin",
    "faculty": "Science"
  }
]
```

### Register Student

```
POST /users/register-student/
```

Registers a new student with a user account.

**Request:**
```json
{
  "email": "student@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "matric_number": "CS/2022/001",
  "faculty": "Engineering",
  "department": "Computer Science",
  "class_year": "300",
  "course": "Computer Engineering",
  "grade": "2.1"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "matric_number": "CS/2022/001",
  "faculty": "Engineering",
  "department": "Computer Science",
  "class_year": "300"
}
```

### Register Admin

```
POST /users/register-admin/
```

Registers a new admin with a user account (requires superuser permissions).

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword123",
  "first_name": "Jane",
  "last_name": "Smith",
  "username": "jsmith",
  "faculty": "Engineering"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "email": "admin@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "username": "jsmith",
  "faculty": "Engineering"
}
```

## Student Management

### List Students

```
GET /users/students/
```

Returns a paginated list of students.

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/users/students/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-string",
      "user": {
        "id": "uuid-string",
        "email": "student1@example.com"
      },
      "first_name": "John",
      "last_name": "Doe",
      "matric_number": "CS/2022/001",
      "faculty": "Engineering",
      "department": "Computer Science",
      "class_year": "300",
      "course": "Computer Engineering",
      "grade": "2.1",
      "face_image": "/media/student_faces/student1.jpg"
    },
    {
      "id": "uuid-string",
      "user": {
        "id": "uuid-string",
        "email": "student2@example.com"
      },
      "first_name": "Jane",
      "last_name": "Smith",
      "matric_number": "CS/2022/002",
      "faculty": "Engineering",
      "department": "Computer Science",
      "class_year": "300",
      "course": "Computer Engineering",
      "grade": "2.1",
      "face_image": "/media/student_faces/student2.jpg"
    }
  ]
}
```

### Get Student Details

```
GET /users/students/{id}/
```

Returns details for a specific student.

**Response:**
```json
{
  "id": "uuid-string",
  "user": {
    "id": "uuid-string",
    "email": "student1@example.com"
  },
  "first_name": "John",
  "last_name": "Doe",
  "matric_number": "CS/2022/001",
  "faculty": "Engineering",
  "department": "Computer Science",
  "class_year": "300",
  "course": "Computer Engineering",
  "grade": "2.1",
  "face_image": "/media/student_faces/student1.jpg"
}
```

### Update Student

```
PUT /users/students/{id}/
```

Updates a student's information.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "matric_number": "CS/2022/001",
  "faculty": "Engineering",
  "department": "Computer Science",
  "class_year": "400",
  "course": "Computer Engineering",
  "grade": "2.1"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "user": {
    "id": "uuid-string",
    "email": "student1@example.com"
  },
  "first_name": "John",
  "last_name": "Doe",
  "matric_number": "CS/2022/001",
  "faculty": "Engineering",
  "department": "Computer Science",
  "class_year": "400",
  "course": "Computer Engineering",
  "grade": "2.1",
  "face_image": "/media/student_faces/student1.jpg"
}
```

### Delete Student

```
DELETE /users/students/{id}/
```

Deletes a student.

**Response:**
```
204 No Content
```

## Face Recognition

### Recognize Face

```
POST /recognition/recognize/
```

Recognizes a face from an uploaded image (no authentication required).

**Request:**
- Content-Type: multipart/form-data
- Body: `image` (file)

**Success Response (200):**
```json
{
  "success": true,
  "confidence": 0.95,
  "user": {
    "id": "uuid-string",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "matric_number": "CS/2022/001",
    "department": "Computer Science",
    "class_year": "300"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

**Error Response (No Face Detected - 400):**
```json
{
  "success": false,
  "error": "No face detected in the image"
}
```

**Error Response (No Match Found - 404):**
```json
{
  "success": false,
  "error": "No matching student found",
  "confidence": 0.3
}
```

### Register Face

```
POST /recognition/register_face/
```

Registers a face image for a student (authentication required).

**Request:**
- Content-Type: multipart/form-data
- Body: 
  - `image` (file): Face image to register
  - `student_id` (string): UUID of the student

**Success Response (200):**
```json
{
  "success": true,
  "message": "Face registered successfully",
  "student": {
    "id": "uuid-string",
    "first_name": "John",
    "last_name": "Doe",
    "matric_number": "CS/2022/001"
  }
}
```

**Error Response (No Face Detected - 400):**
```json
{
  "success": false,
  "error": "No face detected in the image"
}
```

## Recognition Logs

### List Recognition Logs

```
GET /recognition/
```

Returns a paginated list of recognition logs (authentication required).

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/recognition/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-string",
      "student": {
        "id": "uuid-string",
        "first_name": "John",
        "last_name": "Doe",
        "matric_number": "CS/2022/001"
      },
      "timestamp": "2023-04-01T10:30:00Z",
      "confidence": 0.95,
      "success": true,
      "image": "/media/recognition_logs/image1.jpg",
      "processing_time": 0.25
    },
    {
      "id": "uuid-string",
      "student": null,
      "timestamp": "2023-04-01T10:25:00Z",
      "confidence": 0.30,
      "success": false,
      "image": "/media/recognition_logs/image2.jpg",
      "processing_time": 0.22
    }
  ]
}
```

### Get Dashboard Stats

```
GET /recognition/dashboard_stats/
```

Returns recognition statistics for dashboard (authentication required).

**Response:**
```json
{
  "total_recognition_attempts": 1250,
  "successful_recognitions": 1180,
  "failed_recognitions": 70,
  "success_rate": 94.4,
  "average_confidence": 0.89,
  "average_processing_time": 0.23,
  "daily_stats": [
    {
      "date": "2023-04-01",
      "total": 150,
      "successful": 142,
      "failed": 8
    },
    {
      "date": "2023-04-02",
      "total": 143,
      "successful": 138,
      "failed": 5
    }
  ]
}
```

## Error Responses

The API returns standard HTTP status codes along with error messages:

- **400 Bad Request**: Invalid input or request format
- **401 Unauthorized**: Authentication required or invalid credentials
- **403 Forbidden**: Authenticated user lacks required permissions
- **404 Not Found**: Requested resource not found
- **500 Internal Server Error**: Server-side error

All error responses follow this format:

```json
{
  "error": "Error message describing the issue",
  "details": {} // Optional additional details
}
```

## Pagination

List endpoints return paginated results with the following format:

```json
{
  "count": 100, // Total number of items
  "next": "http://localhost:8000/api/endpoint?page=2", // URL for next page (null if last page)
  "previous": null, // URL for previous page (null if first page)
  "results": [] // Array of items for current page
}
```

## Notes

- All date/time values are returned in ISO 8601 format with UTC timezone: `YYYY-MM-DDTHH:MM:SSZ`
- Binary data like images are returned as URLs
- All IDs are UUIDs represented as strings 