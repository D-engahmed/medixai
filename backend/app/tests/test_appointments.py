"""
Appointment management tests
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Dict
from datetime import datetime, timedelta

pytestmark = pytest.mark.asyncio

async def test_create_appointment(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test creating an appointment"""
    response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["scheduled_at"] == test_data["appointment"]["scheduled_at"]
    assert data["duration_minutes"] == test_data["appointment"]["duration_minutes"]
    assert data["status"] == "PENDING"

async def test_get_appointment(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test getting an appointment"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Get the appointment
    response = await client.get(f"/api/v1/appointments/{appointment_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == appointment_id
    assert data["scheduled_at"] == test_data["appointment"]["scheduled_at"]

async def test_update_appointment(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test updating an appointment"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Update the appointment
    new_time = (datetime.now() + timedelta(days=2)).isoformat()
    update_data = {
        "scheduled_at": new_time,
        "duration_minutes": 45
    }
    response = await client.patch(f"/api/v1/appointments/{appointment_id}", 
        headers=auth_headers,
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["scheduled_at"] == new_time
    assert data["duration_minutes"] == 45

async def test_cancel_appointment(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test canceling an appointment"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Cancel the appointment
    response = await client.post(f"/api/v1/appointments/{appointment_id}/cancel", 
        headers=auth_headers,
        json={"reason": "Schedule conflict"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "CANCELLED"
    assert data["cancelled_at"] is not None

async def test_get_doctor_availability(client: AsyncClient, auth_headers: Dict, test_doctor: Dict):
    """Test getting doctor availability"""
    doctor_id = test_doctor["user"].id
    response = await client.get(f"/api/v1/appointments/availability/{doctor_id}", 
        headers=auth_headers,
        params={
            "date": datetime.now().date().isoformat()
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "available_slots" in data
    assert isinstance(data["available_slots"], list)

async def test_get_appointments_by_date_range(client: AsyncClient, auth_headers: Dict):
    """Test getting appointments by date range"""
    start_date = datetime.now().date().isoformat()
    end_date = (datetime.now() + timedelta(days=7)).date().isoformat()
    response = await client.get("/api/v1/appointments", 
        headers=auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "appointments" in data
    assert isinstance(data["appointments"], list)

async def test_get_upcoming_appointments(client: AsyncClient, auth_headers: Dict):
    """Test getting upcoming appointments"""
    response = await client.get("/api/v1/appointments/upcoming", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "appointments" in data
    assert isinstance(data["appointments"], list)

async def test_get_past_appointments(client: AsyncClient, auth_headers: Dict):
    """Test getting past appointments"""
    response = await client.get("/api/v1/appointments/past", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "appointments" in data
    assert isinstance(data["appointments"], list)

async def test_add_appointment_note(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test adding a note to an appointment"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Add a note
    note = {
        "content": "Test note content",
        "type": "GENERAL"
    }
    response = await client.post(f"/api/v1/appointments/{appointment_id}/notes", 
        headers=auth_headers,
        json=note
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content"] == note["content"]
    assert data["type"] == note["type"]

async def test_get_appointment_notes(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test getting appointment notes"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Get notes
    response = await client.get(f"/api/v1/appointments/{appointment_id}/notes", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "notes" in data
    assert isinstance(data["notes"], list)

async def test_update_appointment_status(client: AsyncClient, doctor_auth_headers: Dict, test_data: Dict):
    """Test updating appointment status"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=doctor_auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Update status
    response = await client.patch(f"/api/v1/appointments/{appointment_id}/status", 
        headers=doctor_auth_headers,
        json={"status": "COMPLETED"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "COMPLETED"

async def test_get_appointment_history(client: AsyncClient, auth_headers: Dict, test_data: Dict):
    """Test getting appointment history"""
    # First create an appointment
    create_response = await client.post("/api/v1/appointments", 
        headers=auth_headers,
        json=test_data["appointment"]
    )
    appointment_id = create_response.json()["id"]
    
    # Get history
    response = await client.get(f"/api/v1/appointments/{appointment_id}/history", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)

async def test_get_appointment_reminders(client: AsyncClient, auth_headers: Dict):
    """Test getting appointment reminders"""
    response = await client.get("/api/v1/appointments/reminders", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "reminders" in data
    assert isinstance(data["reminders"], list)

async def test_update_reminder_preferences(client: AsyncClient, auth_headers: Dict):
    """Test updating reminder preferences"""
    preferences = {
        "email_reminders": True,
        "sms_reminders": False,
        "reminder_time": "24h"
    }
    response = await client.put("/api/v1/appointments/reminder-preferences", 
        headers=auth_headers,
        json=preferences
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email_reminders"] == preferences["email_reminders"]
    assert data["sms_reminders"] == preferences["sms_reminders"]
    assert data["reminder_time"] == preferences["reminder_time"]

async def test_get_doctor_schedule(client: AsyncClient, doctor_auth_headers: Dict):
    """Test getting doctor schedule"""
    response = await client.get("/api/v1/appointments/schedule", headers=doctor_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "schedule" in data
    assert isinstance(data["schedule"], dict)

async def test_update_doctor_schedule(client: AsyncClient, doctor_auth_headers: Dict):
    """Test updating doctor schedule"""
    schedule = {
        "monday": [
            {"start": "09:00", "end": "12:00"},
            {"start": "14:00", "end": "17:00"}
        ],
        "tuesday": [
            {"start": "09:00", "end": "12:00"},
            {"start": "14:00", "end": "17:00"}
        ]
    }
    response = await client.put("/api/v1/appointments/schedule", 
        headers=doctor_auth_headers,
        json=schedule
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["schedule"] == schedule
