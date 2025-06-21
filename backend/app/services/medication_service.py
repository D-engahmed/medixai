"""
Medication service
"""
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import shortuuid

from app.models.medication import (
    Medication, InventoryTransaction, Order, OrderItem,
    Prescription, PrescriptionMedication
)
from app.schemas.medication import (
    MedicationCreate, MedicationUpdate, InventoryTransactionCreate,
    OrderCreate, PrescriptionCreate, OrderStatus, PaymentStatus,
    PrescriptionStatus
)
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService

class MedicationService:
    def __init__(
        self,
        db: Session,
        notification_service: NotificationService,
        payment_service: PaymentService
    ):
        self.db = db
        self.notification_service = notification_service
        self.payment_service = payment_service

    def get_medication(self, medication_id: UUID) -> Optional[Medication]:
        """Get medication by ID"""
        return self.db.query(Medication).filter(Medication.id == medication_id).first()

    def search_medications(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        requires_prescription: Optional[bool] = None,
        in_stock: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Medication], int]:
        """Search medications with filters"""
        query_obj = self.db.query(Medication)
        
        if query:
            query_obj = query_obj.filter(
                or_(
                    Medication.name.ilike(f"%{query}%"),
                    Medication.generic_name.ilike(f"%{query}%"),
                    Medication.brand_name.ilike(f"%{query}%"),
                    Medication.description.ilike(f"%{query}%")
                )
            )
            
        if category:
            query_obj = query_obj.filter(Medication.category == category)
            
        if type:
            query_obj = query_obj.filter(Medication.type == type)
            
        if manufacturer:
            query_obj = query_obj.filter(Medication.manufacturer == manufacturer)
            
        if requires_prescription is not None:
            query_obj = query_obj.filter(
                Medication.prescription_requirement == "required"
                if requires_prescription else
                Medication.prescription_requirement != "required"
            )
            
        if in_stock is not None:
            query_obj = query_obj.filter(
                Medication.stock_quantity > 0 if in_stock else Medication.stock_quantity == 0
            )

        total = query_obj.count()
        medications = query_obj.offset((page - 1) * per_page).limit(per_page).all()
        
        return medications, total

    def create_medication(self, medication_data: MedicationCreate) -> Medication:
        """Create a new medication"""
        medication = Medication(**medication_data.dict())
        self.db.add(medication)
        self.db.commit()
        self.db.refresh(medication)
        return medication

    def update_medication(
        self,
        medication_id: UUID,
        medication_data: MedicationUpdate
    ) -> Medication:
        """Update a medication"""
        medication = self.get_medication(medication_id)
        if not medication:
            raise ValueError("Medication not found")

        for field, value in medication_data.dict(exclude_unset=True).items():
            setattr(medication, field, value)

        self.db.commit()
        self.db.refresh(medication)
        return medication

    def create_inventory_transaction(
        self,
        transaction_data: InventoryTransactionCreate,
        user_id: UUID
    ) -> InventoryTransaction:
        """Create an inventory transaction"""
        medication = self.get_medication(transaction_data.medication_id)
        if not medication:
            raise ValueError("Medication not found")

        # Calculate total amount
        total_amount = transaction_data.quantity * transaction_data.unit_price

        # Create transaction
        transaction = InventoryTransaction(
            **transaction_data.dict(),
            total_amount=total_amount,
            created_by=user_id
        )
        self.db.add(transaction)

        # Update medication stock
        if transaction_data.type == "purchase":
            medication.stock_quantity += transaction_data.quantity
        elif transaction_data.type == "sale":
            if medication.stock_quantity < transaction_data.quantity:
                raise ValueError("Insufficient stock")
            medication.stock_quantity -= transaction_data.quantity
        elif transaction_data.type == "adjustment":
            medication.stock_quantity = transaction_data.quantity
        elif transaction_data.type == "return":
            medication.stock_quantity += transaction_data.quantity

        self.db.commit()
        self.db.refresh(transaction)

        # Send notifications for low stock
        if medication.stock_quantity <= medication.minimum_stock:
            self.notification_service.send_low_stock_notification(medication)

        return transaction

    def create_order(
        self,
        user_id: UUID,
        order_data: OrderCreate
    ) -> Order:
        """Create a new order"""
        # Generate order number
        order_number = f"ORD-{shortuuid.uuid()[:8].upper()}"

        # Calculate amounts
        subtotal = 0
        tax = 0
        items = []
        requires_prescription = False

        for item_data in order_data.items:
            medication = self.get_medication(item_data.medication_id)
            if not medication:
                raise ValueError(f"Medication {item_data.medication_id} not found")

            if medication.stock_quantity < item_data.quantity:
                raise ValueError(
                    f"Insufficient stock for medication {medication.name}"
                )

            # Check prescription requirement
            if medication.prescription_requirement == "required":
                requires_prescription = True
                if not order_data.prescription_id:
                    raise ValueError(
                        f"Prescription required for medication {medication.name}"
                    )

            # Calculate item amounts
            unit_price = medication.unit_price
            item_subtotal = unit_price * item_data.quantity
            item_tax = item_subtotal * (medication.tax_rate / 100)
            
            # Calculate insurance coverage if applicable
            insurance_coverage = 0
            if (
                order_data.insurance_provider and
                order_data.insurance_provider in medication.insurance_coverage
            ):
                coverage = medication.insurance_coverage[order_data.insurance_provider]
                insurance_coverage = (
                    item_subtotal * (coverage.coverage_percentage / 100)
                )

            # Create order item
            item = OrderItem(
                medication_id=medication.id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
                tax=item_tax,
                insurance_coverage=insurance_coverage,
                total=item_subtotal + item_tax - insurance_coverage
            )
            items.append(item)

            subtotal += item_subtotal
            tax += item_tax

        # Calculate shipping fee based on method
        shipping_fee = self._calculate_shipping_fee(
            order_data.shipping_method,
            subtotal
        )

        # Create order
        order = Order(
            user_id=user_id,
            order_number=order_number,
            status=OrderStatus.PENDING,
            requires_prescription=requires_prescription,
            prescription_id=order_data.prescription_id,
            prescription_verified=False,
            subtotal=subtotal,
            tax=tax,
            shipping_fee=shipping_fee,
            total=subtotal + tax + shipping_fee,
            payment_status=PaymentStatus.PENDING,
            payment_method=order_data.payment_method,
            shipping_address=order_data.shipping_address.dict(),
            shipping_method=order_data.shipping_method,
            insurance_provider=order_data.insurance_provider,
            insurance_policy_number=order_data.insurance_policy_number
        )

        self.db.add(order)
        self.db.commit()

        # Add items to order
        for item in items:
            item.order_id = order.id
            self.db.add(item)

        self.db.commit()
        self.db.refresh(order)

        # Create payment
        self.payment_service.create_payment(
            order_id=order.id,
            amount=order.total,
            user_id=user_id,
            payment_method=order_data.payment_method
        )

        # Send notifications
        self.notification_service.send_order_created_notification(order)

        return order

    def _calculate_shipping_fee(
        self,
        shipping_method: str,
        subtotal: float
    ) -> float:
        """Calculate shipping fee based on method and order subtotal"""
        if shipping_method == "standard":
            return 10.0 if subtotal < 100 else 0.0
        elif shipping_method == "express":
            return 20.0
        elif shipping_method == "overnight":
            return 35.0
        else:  # pickup
            return 0.0

    def get_order(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_user_orders(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Order], int]:
        """Get user's orders"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
            
        total = query.count()
        orders = query.order_by(Order.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
            
        return orders, total

    def update_order_status(
        self,
        order_id: UUID,
        status: str,
        tracking_number: Optional[str] = None
    ) -> Order:
        """Update order status"""
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order not found")

        old_status = order.status
        order.status = status

        if status == OrderStatus.CONFIRMED:
            order.confirmed_at = datetime.now()
            
            # Update stock quantities
            for item in order.items:
                medication = self.get_medication(item.medication_id)
                if medication.stock_quantity < item.quantity:
                    raise ValueError(
                        f"Insufficient stock for medication {medication.name}"
                    )
                medication.stock_quantity -= item.quantity
                
        elif status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.now()
            if tracking_number:
                order.tracking_number = tracking_number
                
        elif status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.now()
            
        elif status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.now()
            
            # Restore stock quantities if order was confirmed
            if old_status == OrderStatus.CONFIRMED:
                for item in order.items:
                    medication = self.get_medication(item.medication_id)
                    medication.stock_quantity += item.quantity

            # Handle refund if payment was made
            if order.payment_status == PaymentStatus.PAID:
                self.payment_service.refund_payment(order.payment_id)

        self.db.commit()
        self.db.refresh(order)

        # Send notifications
        self.notification_service.send_order_status_notification(
            order,
            old_status,
            status
        )

        return order

    def create_prescription(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        prescription_data: PrescriptionCreate
    ) -> Prescription:
        """Create a new prescription"""
        # Generate prescription number
        prescription_number = f"RX-{shortuuid.uuid()[:8].upper()}"

        # Create prescription
        prescription = Prescription(
            prescription_number=prescription_number,
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=prescription_data.diagnosis,
            notes=prescription_data.notes,
            issue_date=prescription_data.issue_date,
            expiry_date=prescription_data.expiry_date,
            max_uses=prescription_data.max_uses,
            image_urls=prescription_data.image_urls,
            verification_status=PrescriptionStatus.PENDING
        )
        self.db.add(prescription)
        self.db.commit()

        # Add medications to prescription
        for med_data in prescription_data.medications:
            medication = self.get_medication(med_data.medication_id)
            if not medication:
                raise ValueError(f"Medication {med_data.medication_id} not found")

            prescription_med = PrescriptionMedication(
                prescription_id=prescription.id,
                **med_data.dict()
            )
            self.db.add(prescription_med)

        self.db.commit()
        self.db.refresh(prescription)

        # Send notifications
        self.notification_service.send_prescription_created_notification(prescription)

        return prescription

    def verify_prescription(
        self,
        prescription_id: UUID,
        verified_by: UUID,
        approve: bool
    ) -> Prescription:
        """Verify a prescription"""
        prescription = self.db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()
        
        if not prescription:
            raise ValueError("Prescription not found")

        prescription.verification_status = (
            PrescriptionStatus.VERIFIED if approve else PrescriptionStatus.REJECTED
        )
        prescription.verified_by = verified_by
        prescription.verified_at = datetime.now()

        self.db.commit()
        self.db.refresh(prescription)

        # Send notifications
        self.notification_service.send_prescription_verified_notification(
            prescription,
            approve
        )

        return prescription

    def get_prescription(self, prescription_id: UUID) -> Optional[Prescription]:
        """Get prescription by ID"""
        return self.db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()

    def get_patient_prescriptions(
        self,
        patient_id: UUID,
        active_only: bool = False,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Prescription], int]:
        """Get patient's prescriptions"""
        query = self.db.query(Prescription).filter(
            Prescription.patient_id == patient_id
        )
        
        if active_only:
            query = query.filter(
                Prescription.is_valid == True,
                Prescription.expiry_date > datetime.now(),
                Prescription.times_used < Prescription.max_uses,
                Prescription.verification_status == PrescriptionStatus.VERIFIED
            )
            
        total = query.count()
        prescriptions = query.order_by(Prescription.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
            
        return prescriptions, total

    def get_doctor_prescriptions(
        self,
        doctor_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Prescription], int]:
        """Get doctor's prescriptions"""
        query = self.db.query(Prescription).filter(
            Prescription.doctor_id == doctor_id
        )
        
        total = query.count()
        prescriptions = query.order_by(Prescription.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
            
        return prescriptions, total
