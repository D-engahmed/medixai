# نظام المتابعة الطبية

## نظرة عامة
نظام المتابعة الطبية يتتبع تقدم المريض وتفاعلاته مع النظام، بما في ذلك المواعيد، الوصفات الطبية، والمحادثات.

## هيكل النظام

### المكونات الرئيسية
```
app/
├── models/
│   ├── follow_up.py         # نموذج المتابعة
│   └── progress.py          # نموذج التقدم
├── schemas/
│   └── follow_up.py        # مخططات المتابعة
├── api/v1/
│   └── follow_up.py        # نقاط نهاية المتابعة
└── services/
    └── follow_up_service.py # خدمات المتابعة
```

## نماذج البيانات

### نموذج المتابعة
```python
class FollowUp(Base):
    __tablename__ = "follow_ups"
    
    id = Column(UUID, primary_key=True)
    patient_id = Column(UUID, ForeignKey("patients.id"))
    doctor_id = Column(UUID, ForeignKey("doctors.id"))
    appointment_id = Column(UUID, ForeignKey("appointments.id"))
    status = Column(Enum(FollowUpStatus))
    type = Column(Enum(FollowUpType))
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    reminders_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # العلاقات
    patient = relationship("Patient", back_populates="follow_ups")
    doctor = relationship("Doctor", back_populates="follow_ups")
    progress_records = relationship("ProgressRecord", back_populates="follow_up")
```

### نموذج سجل التقدم
```python
class ProgressRecord(Base):
    __tablename__ = "progress_records"
    
    id = Column(UUID, primary_key=True)
    follow_up_id = Column(UUID, ForeignKey("follow_ups.id"))
    record_type = Column(Enum(RecordType))
    metrics = Column(JSONB)
    notes = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    follow_up = relationship("FollowUp", back_populates="progress_records")
```

## خدمات النظام

### خدمة المتابعة
```python
class FollowUpService:
    async def create_follow_up(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        data: FollowUpCreate
    ) -> FollowUp:
        """إنشاء متابعة جديدة"""
        
    async def update_progress(
        self,
        follow_up_id: UUID,
        data: ProgressUpdate
    ) -> ProgressRecord:
        """تحديث تقدم المتابعة"""
        
    async def schedule_reminder(
        self,
        follow_up_id: UUID,
        reminder_type: ReminderType
    ) -> None:
        """جدولة تذكير للمتابعة"""
```

## تدفقات العمل

### إنشاء متابعة جديدة
1. التحقق من العلاقة بين المريض والطبيب
2. إنشاء سجل المتابعة
3. جدولة التذكيرات
4. إخطار المريض والطبيب

### تحديث التقدم
1. التحقق من صلاحية المتابعة
2. تسجيل القياسات الجديدة
3. تحليل التقدم
4. تحديث حالة المتابعة
5. إرسال التقارير

### إدارة التذكيرات
1. تحديد مواعيد التذكير
2. إنشاء رسائل التذكير
3. إرسال الإشعارات
4. تتبع الاستجابة

## الجدولة والتذكيرات

### جدولة المتابعة
```python
class FollowUpScheduler:
    async def schedule_follow_up(
        self,
        follow_up: FollowUp
    ) -> List[ScheduledReminder]:
        """جدولة مواعيد المتابعة والتذكيرات"""
        
    async def reschedule_follow_up(
        self,
        follow_up_id: UUID,
        new_date: datetime
    ) -> FollowUp:
        """إعادة جدولة المتابعة"""
```

### نظام التذكيرات
```python
class ReminderSystem:
    async def create_reminder(
        self,
        follow_up: FollowUp,
        reminder_type: ReminderType
    ) -> Reminder:
        """إنشاء تذكير جديد"""
        
    async def process_reminders(self) -> None:
        """معالجة التذكيرات المستحقة"""
```

## التحليل والتقارير

### تحليل التقدم
```python
class ProgressAnalyzer:
    async def analyze_progress(
        self,
        follow_up_id: UUID
    ) -> ProgressAnalysis:
        """تحليل تقدم المريض"""
        
    async def generate_trends(
        self,
        patient_id: UUID,
        metric_type: str
    ) -> List[Trend]:
        """تحليل اتجاهات التقدم"""
```

### إنشاء التقارير
```python
class ReportGenerator:
    async def generate_progress_report(
        self,
        follow_up_id: UUID
    ) -> Report:
        """إنشاء تقرير التقدم"""
        
    async def generate_summary_report(
        self,
        patient_id: UUID,
        date_range: DateRange
    ) -> Report:
        """إنشاء تقرير ملخص"""
```

## التكامل مع الأنظمة الأخرى

### نظام المواعيد
```python
async def sync_with_appointments(
    follow_up: FollowUp
) -> None:
    """مزامنة المتابعة مع نظام المواعيد"""
```

### نظام الإشعارات
```python
async def send_follow_up_notifications(
    follow_up: FollowUp,
    notification_type: NotificationType
) -> None:
    """إرسال إشعارات المتابعة"""
```

## الاختبارات

### اختبارات الوحدة
```python
class TestFollowUpSystem:
    async def test_follow_up_creation(self):
        """اختبار إنشاء متابعة"""
        
    async def test_progress_tracking(self):
        """اختبار تتبع التقدم"""
```

### اختبارات التكامل
```python
class TestFollowUpIntegration:
    async def test_reminder_system(self):
        """اختبار نظام التذكيرات"""
        
    async def test_reporting_system(self):
        """اختبار نظام التقارير"""
```

## واجهة المستخدم

### عرض المتابعات
```typescript
interface FollowUpView {
    id: string;
    patient: PatientInfo;
    doctor: DoctorInfo;
    status: FollowUpStatus;
    progress: ProgressRecord[];
    nextReminder: Date;
    metrics: MetricChart[];
}
```

### لوحة التحكم
```typescript
interface FollowUpDashboard {
    activeFollowUps: number;
    upcomingReminders: Reminder[];
    recentProgress: ProgressUpdate[];
    alerts: Alert[];
}
``` 