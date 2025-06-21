"""
Payment service for handling all payment operations
"""
from typing import Dict, Any, Optional
from datetime import datetime
import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User
from app.utils.logger import logger

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        user_id: str,
        payment_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent"""
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                customer=self._get_or_create_customer(user),
                metadata={
                    "user_id": user_id,
                    "payment_type": payment_type,
                    **(metadata or {})
                }
            )

            # Store payment intent in database
            payment = Payment(
                id=intent.id,
                user_id=user_id,
                amount=amount,
                currency=currency,
                payment_type=payment_type,
                status=intent.status,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            self.db.add(payment)
            self.db.commit()

            return {
                "client_secret": intent.client_secret,
                "payment_id": intent.id,
                "status": intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create payment"
            )

    def _get_or_create_customer(self, user: User) -> str:
        """Get existing Stripe customer or create new one"""
        try:
            if user.stripe_customer_id:
                return user.stripe_customer_id

            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={"user_id": user.id}
            )

            # Update user with Stripe customer ID
            user.stripe_customer_id = customer.id
            self.db.commit()

            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise

    async def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, str]:
        """Handle Stripe webhook events"""
        try:
            event_type = event_data["type"]
            event_object = event_data["data"]["object"]

            if event_type == "payment_intent.succeeded":
                await self._handle_payment_success(event_object)
            elif event_type == "payment_intent.payment_failed":
                await self._handle_payment_failure(event_object)
            elif event_type == "charge.refunded":
                await self._handle_refund(event_object)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process webhook"
            )

    async def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> None:
        """Handle successful payment"""
        try:
            # Update payment status in database
            payment = self.db.query(Payment).filter(
                Payment.id == payment_intent["id"]
            ).first()

            if payment:
                payment.status = "succeeded"
                payment.completed_at = datetime.utcnow()
                self.db.commit()

                # Update related records based on payment type
                if payment.payment_type == "APPOINTMENT":
                    await self._update_appointment_payment(payment)
                elif payment.payment_type == "MEDICATION":
                    await self._update_medication_order_payment(payment)

        except Exception as e:
            logger.error(f"Error handling payment success: {str(e)}")
            raise

    async def _handle_payment_failure(self, payment_intent: Dict[str, Any]) -> None:
        """Handle failed payment"""
        try:
            # Update payment status in database
            payment = self.db.query(Payment).filter(
                Payment.id == payment_intent["id"]
            ).first()

            if payment:
                payment.status = "failed"
                payment.error = payment_intent.get("last_payment_error", {}).get("message")
                payment.updated_at = datetime.utcnow()
                self.db.commit()

        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            raise

    async def _handle_refund(self, charge: Dict[str, Any]) -> None:
        """Handle refund"""
        try:
            # Update payment status in database
            payment = self.db.query(Payment).filter(
                Payment.charge_id == charge["id"]
            ).first()

            if payment:
                payment.status = "refunded"
                payment.refunded_at = datetime.utcnow()
                self.db.commit()

                # Update related records based on payment type
                if payment.payment_type == "APPOINTMENT":
                    await self._update_appointment_refund(payment)
                elif payment.payment_type == "MEDICATION":
                    await self._update_medication_order_refund(payment)

        except Exception as e:
            logger.error(f"Error handling refund: {str(e)}")
            raise

    async def _update_appointment_payment(self, payment: Any) -> None:
        """Update appointment after successful payment"""
        try:
            appointment_id = payment.metadata.get("appointment_id")
            if appointment_id:
                appointment = self.db.query(Appointment).filter(
                    Appointment.id == appointment_id
                ).first()

                if appointment:
                    appointment.payment_status = "PAID"
                    appointment.status = "CONFIRMED"
                    self.db.commit()

        except Exception as e:
            logger.error(f"Error updating appointment payment: {str(e)}")
            raise

    async def _update_medication_order_payment(self, payment: Any) -> None:
        """Update medication order after successful payment"""
        try:
            order_id = payment.metadata.get("order_id")
            if order_id:
                order = self.db.query(MedicationOrder).filter(
                    MedicationOrder.id == order_id
                ).first()

                if order:
                    order.payment_status = "PAID"
                    order.status = "PROCESSING"
                    self.db.commit()

        except Exception as e:
            logger.error(f"Error updating medication order payment: {str(e)}")
            raise

    async def _update_appointment_refund(self, payment: Any) -> None:
        """Update appointment after refund"""
        try:
            appointment_id = payment.metadata.get("appointment_id")
            if appointment_id:
                appointment = self.db.query(Appointment).filter(
                    Appointment.id == appointment_id
                ).first()

                if appointment:
                    appointment.payment_status = "REFUNDED"
                    appointment.status = "CANCELLED"
                    self.db.commit()

        except Exception as e:
            logger.error(f"Error updating appointment refund: {str(e)}")
            raise

    async def _update_medication_order_refund(self, payment: Any) -> None:
        """Update medication order after refund"""
        try:
            order_id = payment.metadata.get("order_id")
            if order_id:
                order = self.db.query(MedicationOrder).filter(
                    MedicationOrder.id == order_id
                ).first()

                if order:
                    order.payment_status = "REFUNDED"
                    order.status = "CANCELLED"
                    self.db.commit()

        except Exception as e:
            logger.error(f"Error updating medication order refund: {str(e)}")
            raise

    async def get_payment_history(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        payment_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's payment history"""
        try:
            query = self.db.query(Payment).filter(Payment.user_id == user_id)

            if payment_type:
                query = query.filter(Payment.payment_type == payment_type)

            total = query.count()
            payments = query.order_by(
                Payment.created_at.desc()
            ).offset((page - 1) * per_page).limit(per_page).all()

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "payments": [payment.to_dict() for payment in payments]
            }

        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve payment history"
            )

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Refund payment"""
        try:
            payment = self.db.query(Payment).filter(
                Payment.id == payment_id,
                Payment.status == "succeeded"
            ).first()

            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found or cannot be refunded"
                )

            # Create refund in Stripe
            refund_params = {
                "payment_intent": payment_id,
                "reason": reason or "requested_by_customer"
            }
            if amount:
                refund_params["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_params)

            # Update payment status
            payment.status = "refunded"
            payment.refunded_at = datetime.utcnow()
            payment.refund_amount = amount or payment.amount
            payment.refund_reason = reason
            self.db.commit()

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": payment.refund_amount
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error refunding payment: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Refund error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error refunding payment: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process refund"
            )
