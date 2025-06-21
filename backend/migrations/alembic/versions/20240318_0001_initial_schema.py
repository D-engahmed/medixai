"""Initial schema

Revision ID: 20240318_0001
Revises: 
Create Date: 2024-03-18 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240318_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### users table ###
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('two_fa_enabled', sa.Boolean(), default=False),
        sa.Column('two_fa_secret', sa.String(32)),
        sa.Column('preferences', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

    # ### patients table ###
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', postgresql.JSONB),
        sa.Column('medical_history', postgresql.JSONB),
        sa.Column('emergency_contact', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # ### doctors table ###
    op.create_table(
        'doctors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_number', sa.String(50), unique=True, nullable=False),
        sa.Column('specialization', sa.String(100), nullable=False),
        sa.Column('years_experience', sa.Integer),
        sa.Column('consultation_fee', sa.Numeric(10, 2)),
        sa.Column('address', postgresql.JSONB),
        sa.Column('phone', sa.String(20)),
        sa.Column('bio', sa.Text),
        sa.Column('qualifications', postgresql.JSONB),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('rating', sa.Numeric(3, 2)),
        sa.Column('total_reviews', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # ### hospitals table ###
    op.create_table(
        'hospitals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', postgresql.JSONB, nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        sa.Column('services', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

    # ### appointments table ###
    op.create_table(
        'appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('fee', sa.Numeric(10, 2)),
        sa.Column('payment_status', sa.String(20)),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE')
    )

    # ### medications table ###
    op.create_table(
        'medications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('generic_name', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('manufacturer', sa.String(255)),
        sa.Column('type', sa.String(50)),
        sa.Column('dosage_forms', postgresql.JSONB),
        sa.Column('side_effects', postgresql.JSONB),
        sa.Column('contraindications', postgresql.JSONB),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.Column('prescription_required', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

    # ### prescriptions table ###
    op.create_table(
        'prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dosage', sa.Text, nullable=False),
        sa.Column('frequency', sa.Text, nullable=False),
        sa.Column('duration_days', sa.Integer, nullable=False),
        sa.Column('instructions', sa.Text),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ondelete='CASCADE')
    )

    # ### chat_sessions table ###
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('context', postgresql.JSONB),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE')
    )

    # ### chat_messages table ###
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(20), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True)),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('is_escalation_trigger', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE')
    )

    # ### Create indexes ###
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_doctors_license_number', 'doctors', ['license_number'])
    op.create_index('ix_appointments_scheduled_at', 'appointments', ['scheduled_at'])
    op.create_index('ix_chat_sessions_patient_id', 'chat_sessions', ['patient_id'])
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_medications_name', 'medications', ['name'])


def downgrade() -> None:
    # ### Drop tables ###
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('prescriptions')
    op.drop_table('medications')
    op.drop_table('appointments')
    op.drop_table('hospitals')
    op.drop_table('doctors')
    op.drop_table('patients')
    op.drop_table('users') 