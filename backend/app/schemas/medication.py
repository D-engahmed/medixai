"""
Medication schemas
"""
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, validator, constr
from enum import Enum

class MedicationType(str, Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    INJECTION = "injection"
    CREAM = "cream"
    DROPS = "drops"
    INHALER = "inhaler"
    POWDER = "powder"
    PATCH = "patch"

class MedicationCategory(str, Enum):
    PRESCRIPTION = "prescription"
    OTC = "otc"
    CONTROLLED = "controlled"

class PrescriptionRequirement(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    NOT_REQUIRED = "not_required"

class StorageCondition(str, Enum):
    ROOM_TEMPERATURE = "room_temperature"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"
    COOL_DRY = "cool_dry"
    PROTECTED_FROM_LIGHT = "protected_from_light"

class ActiveIngredient(BaseModel):
    name: str
    amount: str
    unit: str

class InsuranceCoverage(BaseModel):
    provider: str
    coverage_percentage: float = Field(ge=0, le=100)
    requires_pre_approval: bool = False
    coverage_limit: Optional[float] = None
    policy_details: Optional[Dict] = None

class MedicationBase(BaseModel):
    name: str
    generic_name: str
    brand_name: Optional[str]
    manufacturer: str
    type: MedicationType
    category: MedicationCategory
    prescription_requirement: PrescriptionRequirement
    description: str
    dosage_form: str
    active_ingredients: List[ActiveIngredient]
    usage_instructions: str
    side_effects: List[str]
    contraindications: List[str]
    interactions: Dict[str, List[str]]  # Category -> List of interactions
    storage_condition: StorageCondition
    shelf_life_months: int = Field(ge=1)
    requires_cold_chain: bool = False

class MedicationCreate(MedicationBase):
    sku: str
    barcode: Optional[str]
    unit_price: float = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    minimum_stock: int = Field(ge=0)
    maximum_stock: int = Field(ge=0)
    registration_number: Optional[str]
    requires_special_authorization: bool = False
    controlled_substance_class: Optional[str]
    insurance_coverage: Dict[str, InsuranceCoverage] = {}
    discount_eligible: bool = True
    tax_rate: float = Field(ge=0, le=100)
    images: List[str] = []
    package_insert_url: Optional[str]

class MedicationUpdate(BaseModel):
    unit_price: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    insurance_coverage: Optional[Dict[str, InsuranceCoverage]]
    discount_eligible: Optional[bool]
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    images: Optional[List[str]]
    package_insert_url: Optional[str]
    description: Optional[str]
    usage_instructions: Optional[str]
    side_effects: Optional[List[str]]
    contraindications: Optional[List[str]]
    interactions: Optional[Dict[str, List[str]]]

class MedicationResponse(MedicationBase):
    id: UUID
    sku: str
    barcode: Optional[str]
    unit_price: float
    stock_quantity: int
    minimum_stock: int
    maximum_stock: int
    registration_number: Optional[str]
    requires_special_authorization: bool
    controlled_substance_class: Optional[str]
    insurance_coverage: Dict[str, InsuranceCoverage]
    discount_eligible: bool
    tax_rate: float
    images: List[str]
    package_insert_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class InventoryTransactionType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RETURN = "return"

class InventoryTransactionCreate(BaseModel):
    medication_id: UUID
    type: InventoryTransactionType
    quantity: int
    unit_price: float = Field(ge=0)
    batch_number: Optional[str]
    expiration_date: Optional[datetime]
    reference_number: Optional[str]
    notes: Optional[str]

    @validator('expiration_date')
    def validate_expiration_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v

class InventoryTransactionResponse(InventoryTransactionCreate):
    id: UUID
    total_amount: float
    created_at: datetime
    created_by: UUID

    class Config:
        orm_mode = True

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"

class ShippingMethod(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    PICKUP = "pickup"

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: str

class OrderItemCreate(BaseModel):
    medication_id: UUID
    quantity: int = Field(ge=1)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    prescription_id: Optional[UUID]
    shipping_address: Address
    shipping_method: ShippingMethod
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    payment_method: str

class OrderItemResponse(OrderItemCreate):
    id: UUID
    unit_price: float
    subtotal: float
    discount: float
    tax: float
    total: float
    insurance_coverage: float
    medication: MedicationResponse

    class Config:
        orm_mode = True

class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    requires_prescription: bool
    prescription_verified: bool
    subtotal: float
    tax: float
    shipping_fee: float
    discount: float
    total: float
    payment_status: PaymentStatus
    payment_method: Optional[str]
    payment_id: Optional[str]
    shipping_address: Address
    shipping_method: ShippingMethod
    tracking_number: Optional[str]
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    insurance_coverage_amount: float
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        orm_mode = True

class PrescriptionStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class PrescriptionMedicationCreate(BaseModel):
    medication_id: UUID
    dosage: str
    frequency: str
    duration: str
    quantity: int = Field(ge=1)
    instructions: str

class PrescriptionCreate(BaseModel):
    diagnosis: str
    notes: Optional[str]
    medications: List[PrescriptionMedicationCreate]
    issue_date: datetime
    expiry_date: datetime
    max_uses: int = Field(default=1, ge=1)
    image_urls: List[str] = []

    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError("Expiry date must be after issue date")
        return v

class PrescriptionMedicationResponse(PrescriptionMedicationCreate):
    id: UUID
    prescription_id: UUID
    medication: MedicationResponse

    class Config:
        orm_mode = True

class PrescriptionResponse(BaseModel):
    id: UUID
    prescription_number: str
    patient_id: UUID
    doctor_id: UUID
    diagnosis: str
    notes: Optional[str]
    issue_date: datetime
    expiry_date: datetime
    is_valid: bool
    times_used: int
    max_uses: int
    verification_status: PrescriptionStatus
    verified_by: Optional[UUID]
    verified_at: Optional[datetime]
    image_urls: List[str]
    medications: List[PrescriptionMedicationResponse]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
