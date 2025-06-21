"""
Medication endpoints
"""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
    get_current_doctor,
    get_current_admin
)
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    InventoryTransactionCreate,
    InventoryTransactionResponse,
    OrderCreate,
    OrderResponse,
    PrescriptionCreate,
    PrescriptionResponse
)
from app.services.medication_service import MedicationService
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/medications", tags=["medications"])

def get_medication_service(
    db: Session = Depends(get_db),
    notification_service: NotificationService = Depends(),
    payment_service: PaymentService = Depends()
) -> MedicationService:
    return MedicationService(db, notification_service, payment_service)

@router.post("", response_model=MedicationResponse)
async def create_medication(
    medication_data: MedicationCreate,
    current_admin: User = Depends(get_current_admin),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Create a new medication (Admin only)"""
    try:
        return medication_service.create_medication(medication_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[MedicationResponse])
async def search_medications(
    query: Optional[str] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    requires_prescription: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Search medications with filters"""
    medications, total = medication_service.search_medications(
        query,
        category,
        type,
        manufacturer,
        requires_prescription,
        in_stock,
        page,
        per_page
    )
    return medications

@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: UUID,
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get medication by ID"""
    medication = medication_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication

@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    medication_data: MedicationUpdate,
    current_admin: User = Depends(get_current_admin),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Update medication (Admin only)"""
    try:
        return medication_service.update_medication(
            medication_id,
            medication_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/inventory", response_model=InventoryTransactionResponse)
async def create_inventory_transaction(
    transaction_data: InventoryTransactionCreate,
    current_admin: User = Depends(get_current_admin),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Create inventory transaction (Admin only)"""
    try:
        return medication_service.create_inventory_transaction(
            transaction_data,
            current_admin.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Create a new order"""
    try:
        return medication_service.create_order(current_user.id, order_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get user's orders"""
    orders, total = medication_service.get_user_orders(
        current_user.id,
        status,
        page,
        per_page
    )
    return orders

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get order by ID"""
    order = medication_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return order

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status: str,
    tracking_number: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Update order status (Admin only)"""
    try:
        return medication_service.update_order_status(
            order_id,
            status,
            tracking_number
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    patient_id: UUID,
    current_doctor: Doctor = Depends(get_current_doctor),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Create a new prescription (Doctor only)"""
    try:
        return medication_service.create_prescription(
            current_doctor.id,
            patient_id,
            prescription_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/prescriptions/{prescription_id}/verify")
async def verify_prescription(
    prescription_id: UUID,
    approve: bool,
    current_admin: User = Depends(get_current_admin),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Verify prescription (Admin only)"""
    try:
        return medication_service.verify_prescription(
            prescription_id,
            current_admin.id,
            approve
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/prescriptions", response_model=List[PrescriptionResponse])
async def get_patient_prescriptions(
    active_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get patient's prescriptions"""
    prescriptions, total = medication_service.get_patient_prescriptions(
        current_user.id,
        active_only,
        page,
        per_page
    )
    return prescriptions

@router.get("/prescriptions/doctor", response_model=List[PrescriptionResponse])
async def get_doctor_prescriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_doctor: Doctor = Depends(get_current_doctor),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get doctor's prescriptions"""
    prescriptions, total = medication_service.get_doctor_prescriptions(
        current_doctor.id,
        page,
        per_page
    )
    return prescriptions

@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: UUID,
    current_user: User = Depends(get_current_user),
    medication_service: MedicationService = Depends(get_medication_service)
):
    """Get prescription by ID"""
    prescription = medication_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
        
    # Check authorization
    if (
        prescription.patient_id != current_user.id and
        not hasattr(current_user, 'is_doctor') and
        not current_user.is_admin
    ):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return prescription
