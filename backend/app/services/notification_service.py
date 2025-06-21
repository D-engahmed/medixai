"""
Notification service for handling all types of notifications
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from firebase_admin import messaging

from app.config.settings import settings
from app.models.user import User
from app.utils.logger import logger
from app.utils.helpers import render_template

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_sender = settings.EMAIL_SENDER
        self.email_password = settings.EMAIL_PASSWORD
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Send notification to user through multiple channels"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            notification_data = {
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "data": data or {},
                "created_at": datetime.utcnow()
            }

            # Store notification in database
            notification = self._store_notification(notification_data)

            # Send through different channels based on user preferences
            if background_tasks:
                if user.preferences.get("email_notifications", True):
                    background_tasks.add_task(
                        self.send_email_notification,
                        user.email,
                        title,
                        message,
                        notification_type
                    )

                if user.preferences.get("push_notifications", True):
                    background_tasks.add_task(
                        self.send_push_notification,
                        user.id,
                        title,
                        message,
                        data
                    )

                if user.preferences.get("sms_notifications", False) and user.phone:
                    background_tasks.add_task(
                        self.send_sms_notification,
                        user.phone,
                        message
                    )

            return {
                "notification_id": notification.id,
                "status": "queued",
                "channels": self._get_enabled_channels(user)
            }

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send notification: {str(e)}"
            )

    def _store_notification(self, notification_data: Dict[str, Any]) -> Any:
        """Store notification in database"""
        try:
            notification = Notification(
                user_id=notification_data["user_id"],
                type=notification_data["type"],
                title=notification_data["title"],
                message=notification_data["message"],
                data=notification_data["data"],
                created_at=notification_data["created_at"]
            )
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            return notification
        except Exception as e:
            logger.error(f"Error storing notification: {str(e)}")
            self.db.rollback()
            raise

    async def send_email_notification(
        self,
        email: str,
        subject: str,
        message: str,
        template_type: str
    ) -> None:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_sender
            msg["To"] = email
            msg["Subject"] = subject

            # Render HTML template
            html_content = render_template(
                template_type,
                {"message": message}
            )
            msg.attach(MIMEText(html_content, "html"))

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)

            logger.info(f"Email notification sent to {email}")

        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            raise

    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send push notification using Firebase"""
        try:
            # Get user's FCM tokens
            user_tokens = self._get_user_fcm_tokens(user_id)
            if not user_tokens:
                logger.warning(f"No FCM tokens found for user {user_id}")
                return

            message = messaging.MulticastMessage(
                tokens=user_tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {}
            )

            response = messaging.send_multicast(message)
            logger.info(
                f"Push notification sent to {len(user_tokens)} devices. "
                f"Success: {response.success_count}, Failure: {response.failure_count}"
            )

            # Handle failed tokens
            if response.failure_count > 0:
                self._handle_failed_tokens(user_id, response.responses, user_tokens)

        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            raise

    async def send_sms_notification(self, phone: str, message: str) -> None:
        """Send SMS notification using Twilio"""
        try:
            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            # Send SMS
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )

            logger.info(f"SMS notification sent to {phone}, SID: {message.sid}")

        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            raise

    def _get_user_fcm_tokens(self, user_id: str) -> List[str]:
        """Get user's FCM tokens from database"""
        try:
            tokens = self.db.query(FCMToken).filter(
                FCMToken.user_id == user_id,
                FCMToken.is_active == True
            ).all()
            return [token.token for token in tokens]
        except Exception as e:
            logger.error(f"Error getting FCM tokens: {str(e)}")
            return []

    def _handle_failed_tokens(
        self,
        user_id: str,
        responses: List[Any],
        tokens: List[str]
    ) -> None:
        """Handle failed FCM tokens"""
        try:
            for idx, response in enumerate(responses):
                if not response.success:
                    token = tokens[idx]
                    if (
                        response.exception
                        and isinstance(response.exception, messaging.UnregisteredError)
                    ):
                        # Token is no longer valid, deactivate it
                        self.db.query(FCMToken).filter(
                            FCMToken.token == token
                        ).update({"is_active": False})

            self.db.commit()
        except Exception as e:
            logger.error(f"Error handling failed tokens: {str(e)}")
            self.db.rollback()

    def _get_enabled_channels(self, user: User) -> List[str]:
        """Get list of enabled notification channels for user"""
        channels = []
        preferences = user.preferences or {}

        if preferences.get("email_notifications", True):
            channels.append("email")
        if preferences.get("push_notifications", True):
            channels.append("push")
        if preferences.get("sms_notifications", False) and user.phone:
            channels.append("sms")

        return channels

    async def get_user_notifications(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's notifications with pagination"""
        try:
            query = self.db.query(Notification).filter(
                Notification.user_id == user_id
            )

            if notification_type:
                query = query.filter(Notification.type == notification_type)

            total = query.count()
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset((page - 1) * per_page).limit(per_page).all()

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "notifications": [notification.to_dict() for notification in notifications]
            }

        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve notifications"
            )

    async def mark_notification_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()

            if not notification:
                raise HTTPException(
                    status_code=404,
                    detail="Notification not found"
                )

            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()

            return {"status": "success", "message": "Notification marked as read"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to mark notification as read"
            )

    async def delete_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Delete notification"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()

            if not notification:
                raise HTTPException(
                    status_code=404,
                    detail="Notification not found"
                )

            self.db.delete(notification)
            self.db.commit()

            return {"status": "success", "message": "Notification deleted"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete notification"
            )
