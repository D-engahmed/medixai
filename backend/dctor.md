erDiagram
    Doctor ||--o{ DoctorClinic : "has"
    Doctor ||--o{ DoctorHospital : "works_at"
    Doctor ||--o{ DoctorReview : "receives"
    Hospital ||--o{ DoctorHospital : "employs"
    User ||--o{ DoctorReview : "writes"

    Doctor {
        UUID id PK
        UUID user_id FK
        string title
        string first_name
        string last_name
        string gender
        datetime date_of_birth
        string nationality
        string email
        string phone
        string[] languages
        string medical_degree
        string medical_school
        int graduation_year
        string license_number
        datetime license_expiry
        DoctorType type
        int years_of_experience
        string[] specializations
        string[] sub_specializations
        string[] certifications
        ConsultationType[] consultation_types
        int consultation_duration
        int max_patients_per_day
        bool accepting_new_patients
        json consultation_fees
        json follow_up_fees
        json emergency_fees
        string[] insurance_providers
        text bio
        string[] expertise_areas
        string[] research_interests
        string[] publications
        string[] awards
        string profile_image
        string[] additional_images
        string video_intro
        float rating
        int total_reviews
        int total_patients
        float success_rate
        DoctorStatus status
        bool is_verified
        datetime verification_date
        UUID verified_by FK
    }

    DoctorClinic {
        UUID id PK
        UUID doctor_id FK
        string name
        string branch
        text address
        string city
        string state
        string country
        string postal_code
        float latitude
        float longitude
        string phone
        string email
        string website
        json working_hours
        json breaks
        string[] facilities
        string[] services
        string[] payment_methods
        bool insurance_accepted
        string[] images
        string virtual_tour
        bool is_primary
        bool is_active
    }

    Hospital {
        UUID id PK
        string name
        string type
        int established_year
        text address
        string city
        string state
        string country
        string postal_code
        float latitude
        float longitude
        string phone
        string emergency_phone
        string email
        string website
        int bed_capacity
        int icu_beds
        int operating_rooms
        string[] departments
        string[] specialties
        string[] facilities
        string[] services
        int doctors_count
        int nurses_count
        int staff_count
        string[] accreditations
        string[] certifications
        string license_number
        datetime license_expiry
        string[] insurance_providers
        string[] payment_methods
        float rating
        int total_reviews
        string[] images
        string virtual_tour
        string logo
        bool is_active
        bool is_verified
        datetime verification_date
    }

    DoctorHospital {
        UUID id PK
        UUID doctor_id FK
        UUID hospital_id FK
        string department
        string position
        datetime start_date
        datetime end_date
        bool is_primary
        bool is_visiting
        string[] working_days
        json working_hours
        bool on_call_availability
        bool is_active
    }

    DoctorReview {
        UUID id PK
        UUID doctor_id FK
        UUID patient_id FK
        UUID appointment_id FK
        float rating
        text review
        float waiting_time_rating
        float cleanliness_rating
        float staff_rating
        float communication_rating
        float value_rating
        bool would_recommend
        string[] tags
        bool is_verified
        bool is_public
        bool is_anonymous
    }
    