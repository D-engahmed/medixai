# Medical Platform - Complete Backend Architecture

## Project Structure
```
medical-platform/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── database.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── middleware.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── doctor.py
│   │   ├── appointment.py
│   │   ├── medication.py
│   │   └── chat.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── doctor.py
│   │   ├── appointment.py
│   │   └── medication.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── doctors.py
│   │   │   ├── appointments.py
│   │   │   ├── medications.py
│   │   │   ├── chat.py
│   │   │   └── dashboard.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── doctor_service.py
│   │   ├── appointment_service.py
│   │   ├── medication_service.py
│   │   ├── chat_service.py
│   │   ├── geo_service.py
│   │   ├── payment_service.py
│   │   └── notification_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── encryption.py
│   │   ├── logger.py
│   │   └── helpers.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_users.py
│       └── test_appointments.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
│       └── nginx.conf
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── migrations/
│   └── alembic/
├── docs/
│   ├── API.md
│   ├── SECURITY.md
│   └── DEPLOYMENT.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── README.md
└── Makefile
```

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web App]
        MOBILE[Mobile App]
        ADMIN[Admin Dashboard]
    end

    subgraph "API Gateway"
        NGINX[NGINX/Traefik]
        SSL[SSL Termination]
        LB[Load Balancer]
    end

    subgraph "Application Layer"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance 3]
    end

    subgraph "Service Layer"
        AUTH[Auth Service]
        USER[User Service]
        DOC[Doctor Service]
        APPT[Appointment Service]
        MED[Medication Service]
        CHAT[Chat Service]
        GEO[Geo Service]
        PAY[Payment Service]
        NOTIF[Notification Service]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        ELASTIC[(Elasticsearch)]
        S3[(File Storage)]
    end

    subgraph "External Services"
        STRIPE[Stripe API]
        SMS[SMS Gateway]
        EMAIL[Email Service]
        MAPS[Maps API]
        ML[ML Models]
    end

    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end

    WEB --> NGINX
    MOBILE --> NGINX
    ADMIN --> NGINX

    NGINX --> API1
    NGINX --> API2
    NGINX --> API3

    API1 --> AUTH
    API1 --> USER
    API1 --> DOC
    API2 --> APPT
    API2 --> MED
    API2 --> CHAT
    API3 --> GEO
    API3 --> PAY
    API3 --> NOTIF

    AUTH --> POSTGRES
    AUTH --> REDIS
    USER --> POSTGRES
    DOC --> POSTGRES
    APPT --> POSTGRES
    MED --> POSTGRES
    CHAT --> POSTGRES
    CHAT --> ELASTIC

    PAY --> STRIPE
    NOTIF --> SMS
    NOTIF --> EMAIL
    GEO --> MAPS
    CHAT --> ML

    API1 --> PROM
    API2 --> PROM
    API3 --> PROM
    PROM --> GRAF

    API1 --> ELK
    API2 --> ELK
    API3 --> ELK
```

## Database Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ PATIENTS : "is_a"
    USERS ||--o{ DOCTORS : "is_a"
    USERS ||--o{ USER_SESSIONS : "has"
    USERS ||--o{ AUDIT_LOGS : "generates"
    
    PATIENTS ||--o{ APPOINTMENTS : "books"
    PATIENTS ||--o{ MEDICATION_ORDERS : "places"
    PATIENTS ||--o{ CHAT_SESSIONS : "initiates"
    PATIENTS ||--o{ PATIENT_HISTORY : "has"
    
    DOCTORS ||--o{ APPOINTMENTS : "accepts"
    DOCTORS ||--o{ DOCTOR_SPECIALTIES : "has"
    DOCTORS ||--o{ DOCTOR_HOSPITALS : "affiliated_with"
    DOCTORS ||--o{ DOCTOR_AVAILABILITY : "sets"
    DOCTORS ||--o{ PRESCRIPTIONS : "writes"
    
    HOSPITALS ||--o{ DOCTOR_HOSPITALS : "employs"
    SPECIALTIES ||--o{ DOCTOR_SPECIALTIES : "categorizes"
    
    APPOINTMENTS ||--o{ APPOINTMENT_NOTES : "has"
    APPOINTMENTS ||--o{ PRESCRIPTIONS : "results_in"
    
    MEDICATIONS ||--o{ MEDICATION_ORDERS : "ordered"
    MEDICATIONS ||--o{ PRESCRIPTIONS : "prescribed"
    MEDICATIONS ||--o{ DRUG_INTERACTIONS : "interacts_with"
    
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : "contains"
    CHAT_SESSIONS ||--o{ CHAT_ESCALATIONS : "may_escalate"
    
    COUNTRIES ||--o{ MEDICATION_LEGALITY : "regulates"
    MEDICATIONS ||--o{ MEDICATION_LEGALITY : "legal_in"

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        enum role
        boolean is_active
        boolean email_verified
        boolean two_fa_enabled
        string two_fa_secret
        jsonb preferences
        timestamp created_at
        timestamp updated_at
    }

    PATIENTS {
        uuid id PK
        uuid user_id FK
        date date_of_birth
        enum gender
        string phone
        jsonb address
        jsonb medical_history
        jsonb emergency_contact
        timestamp created_at
        timestamp updated_at
    }

    DOCTORS {
        uuid id PK
        uuid user_id FK
        string license_number UK
        string specialization
        integer years_experience
        decimal consultation_fee
        jsonb address
        string phone
        text bio
        jsonb qualifications
        boolean verified
        decimal rating
        integer total_reviews
        timestamp created_at
        timestamp updated_at
    }

    HOSPITALS {
        uuid id PK
        string name
        jsonb address
        string phone
        string email
        string website
        decimal latitude
        decimal longitude
        jsonb services
        timestamp created_at
        timestamp updated_at
    }

    SPECIALTIES {
        uuid id PK
        string name UK
        text description
        timestamp created_at
    }

    APPOINTMENTS {
        uuid id PK
        uuid patient_id FK
        uuid doctor_id FK
        datetime scheduled_at
        integer duration_minutes
        enum status
        enum type
        text reason
        text notes
        decimal fee
        enum payment_status
        uuid payment_id
        timestamp created_at
        timestamp updated_at
        timestamp cancelled_at
    }

    MEDICATIONS {
        uuid id PK
        string name
        string generic_name
        text description
        string manufacturer
        enum type
        jsonb dosage_forms
        jsonb side_effects
        jsonb contraindications
        decimal price
        boolean prescription_required
        timestamp created_at
        timestamp updated_at
    }

    PRESCRIPTIONS {
        uuid id PK
        uuid appointment_id FK
        uuid doctor_id FK
        uuid patient_id FK
        uuid medication_id FK
        text dosage
        text frequency
        integer duration_days
        text instructions
        enum status
        timestamp created_at
        timestamp updated_at
    }

    CHAT_SESSIONS {
        uuid id PK
        uuid patient_id FK
        enum session_type
        enum status
        jsonb context
        timestamp started_at
        timestamp ended_at
        timestamp created_at
        timestamp updated_at
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid session_id FK
        enum sender_type
        uuid sender_id FK
        text message
        jsonb metadata
        boolean is_escalation_trigger
        timestamp created_at
    }
```

## Technology Stack

### Core Technologies
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 with Alembic
- **Cache**: Redis 7+
- **Message Queue**: Celery with Redis
- **Search**: Elasticsearch 8+
- **Container**: Docker & Docker Compose
- **Orchestration**: Kubernetes

### Security
- **Authentication**: JWT with refresh tokens
- **Password Hashing**: Argon2
- **2FA**: TOTP (Time-based OTP)
- **Encryption**: AES-256-GCM for data at rest
- **TLS**: TLS 1.3 minimum

### Monitoring & Observability
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger
- **Health Checks**: Custom health endpoints

### External Integrations
- **Payment**: Stripe API
- **Geolocation**: Google Maps API
- **Email**: SendGrid
- **SMS**: Twilio
- **File Storage**: AWS S3 or MinIO

## Key Features

### Authentication & Authorization
- JWT access tokens (15 min expiry)
- Refresh tokens (30 days expiry)
- Role-based access control (RBAC)
- Optional 2FA for doctors
- Session management with Redis

### Medical Chat System
- RAG system with BioMedX2 model
- Separate general chat model
- Auto-escalation triggers
- Chat history and analytics

### Appointment System
- Real-time availability checking
- Booking conflicts prevention
- Automated notifications
- Calendar integration

### Medication Store
- Country-specific legality checks
- Drug interaction warnings
- Prescription validation
- Payment processing

### Doctor Dashboard
- Patient management
- Revenue analytics
- Appointment scheduling
- Treatment outcomes

### Security Compliance
- GDPR compliant data handling
- HIPAA security requirements
- Audit logging
- Data encryption
- Rate limiting
- Input validation
