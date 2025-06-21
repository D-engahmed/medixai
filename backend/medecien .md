classDiagram
    class Medication {
        +UUID id
        +String name
        +String scientific_name
        +String trade_name
        +String manufacturer
        +String country_of_origin
        +MedicationType type
        +MedicationCategory category
        +Text description
        +String dosage
        +String form
        +String package_size
        +Text usage_instructions
        +String[] side_effects
        +String[] warnings
        +StorageCondition storage_condition
        +Integer shelf_life_months
        +String barcode
        +Decimal price
        +Integer stock_quantity
        +Integer min_stock_level
        +Integer max_stock_level
        +String registration_number
        +Boolean needs_prescription
        +Boolean is_controlled
        +JSON insurance_coverage
        +String[] images
        +String leaflet_url
    }

    class MedicationBatch {
        +UUID id
        +UUID medication_id
        +String batch_number
        +Integer quantity
        +DateTime manufacturing_date
        +DateTime expiry_date
        +Decimal unit_cost
        +String supplier
        +String invoice_number
        +Boolean is_active
        +Text notes
    }

    class Order {
        +UUID id
        +UUID user_id
        +String order_number
        +String status
        +UUID prescription_id
        +Boolean needs_prescription
        +Boolean prescription_verified
        +Decimal subtotal
        +Decimal tax
        +Decimal shipping_fee
        +Decimal discount
        +Decimal total
        +String payment_status
        +String payment_method
        +String payment_id
        +JSON shipping_address
        +String shipping_method
        +String tracking_number
    }

    class OrderItem {
        +UUID id
        +UUID order_id
        +UUID medication_id
        +UUID batch_id
        +Integer quantity
        +Decimal unit_price
        +Decimal subtotal
        +Decimal discount
        +Decimal tax
        +Decimal total
        +Decimal insurance_coverage
    }

    class Prescription {
        +UUID id
        +UUID patient_id
        +UUID doctor_id
        +String prescription_number
        +Text diagnosis
        +Text notes
        +DateTime issue_date
        +DateTime expiry_date
        +Boolean is_valid
        +Integer times_used
        +Integer max_uses
        +String verification_status
        +UUID verified_by
        +DateTime verified_at
        +String[] image_urls
    }

    class PrescriptionItem {
        +UUID id
        +UUID prescription_id
        +UUID medication_id
        +String dosage
        +String frequency
        +String duration
        +Integer quantity
        +Text instructions
    }

    Medication "1" -- "*" MedicationBatch
    Medication "1" -- "*" OrderItem
    Medication "1" -- "*" PrescriptionItem
    Order "1" -- "*" OrderItem
    Order "1" -- "1" Prescription
    Prescription "1" -- "*" PrescriptionItem