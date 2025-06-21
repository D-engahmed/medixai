# نظام المدفوعات

## نظرة عامة
نظام المدفوعات يتعامل مع جميع المعاملات المالية في المنصة، بما في ذلك رسوم الاستشارات، مدفوعات الأدوية، والتسويات مع الأطباء.

## هيكل الملفات
```
app/
├── models/
│   ├── payment.py         # نموذج بيانات المدفوعات
│   └── transaction.py     # نموذج بيانات المعاملات
├── schemas/
│   └── payment.py        # مخططات التحقق من صحة البيانات
├── api/v1/
│   └── payments.py       # نقاط نهاية API الخاصة بالمدفوعات
├── services/
│   ├── payment_service.py # خدمات المدفوعات
│   └── stripe_service.py  # تكامل Stripe
└── utils/
    └── currency.py       # معالجة العملات
```

## نماذج البيانات

### نموذج المدفوعات (Payment Model)
```python
class Payment(Base):
    id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    payment_provider: str
    provider_payment_id: str
    user_id: UUID
    service_type: ServiceType  # CONSULTATION, MEDICATION, etc.
    service_id: UUID
    metadata: JSON
    created_at: datetime
    updated_at: datetime
```

### نموذج المعاملات (Transaction Model)
```python
class Transaction(Base):
    id: UUID
    payment_id: UUID
    type: TransactionType  # CHARGE, REFUND, TRANSFER
    amount: Decimal
    status: TransactionStatus
    provider_transaction_id: str
    metadata: JSON
    created_at: datetime
```

## الخدمات (Services)

### خدمة المدفوعات
```python
class PaymentService:
    async def create_payment(
        amount: Decimal,
        currency: str,
        service_type: ServiceType,
        service_id: UUID,
        user_id: UUID
    ) -> Payment:
        # إنشاء دفعة جديدة
        
    async def process_payment(
        payment_id: UUID,
        payment_method_id: str
    ) -> Payment:
        # معالجة الدفع
        
    async def refund_payment(
        payment_id: UUID,
        amount: Optional[Decimal] = None
    ) -> Transaction:
        # إرجاع المبلغ
```

### خدمة Stripe
```python
class StripeService:
    async def create_payment_intent(
        amount: int,
        currency: str,
        metadata: dict
    ) -> str:
        # إنشاء payment intent في Stripe
        
    async def create_refund(
        charge_id: str,
        amount: Optional[int] = None
    ) -> dict:
        # إنشاء عملية إرجاع في Stripe
```

## نقاط النهاية (API Endpoints)

### المدفوعات
- `POST /api/v1/payments`: إنشاء دفعة جديدة
- `GET /api/v1/payments/{id}`: عرض تفاصيل الدفعة
- `POST /api/v1/payments/{id}/process`: معالجة الدفعة
- `POST /api/v1/payments/{id}/refund`: إرجاع المبلغ

### طرق الدفع
- `GET /api/v1/payment-methods`: عرض طرق الدفع المحفوظة
- `POST /api/v1/payment-methods`: إضافة طريقة دفع جديدة
- `DELETE /api/v1/payment-methods/{id}`: حذف طريقة دفع

### المحفظة والتحويلات
- `GET /api/v1/wallet`: عرض رصيد المحفظة
- `POST /api/v1/wallet/withdraw`: سحب الرصيد
- `GET /api/v1/transfers`: عرض التحويلات

## تدفق البيانات

### عملية الدفع
1. إنشاء دفعة جديدة
   ```python
   payment = await payment_service.create_payment(
       amount=100.00,
       currency="USD",
       service_type=ServiceType.CONSULTATION,
       service_id=appointment_id,
       user_id=patient_id
   )
   ```

2. معالجة الدفع
   ```python
   processed_payment = await payment_service.process_payment(
       payment_id=payment.id,
       payment_method_id=stripe_payment_method_id
   )
   ```

3. تحديث حالة الخدمة
   ```python
   await appointment_service.update_payment_status(
       appointment_id=service_id,
       payment_status=processed_payment.status
   )
   ```

### عملية الإرجاع
1. التحقق من أهلية الإرجاع
2. إنشاء عملية إرجاع
3. تحديث سجلات المعاملات
4. إخطار المستخدم

## معالجة الأخطاء والاستثناءات

### أخطاء المدفوعات
```python
class PaymentError(Exception):
    pass

class InsufficientFundsError(PaymentError):
    pass

class PaymentMethodError(PaymentError):
    pass

class RefundError(PaymentError):
    pass
```

### معالجة الأخطاء
```python
async def handle_payment_error(error: PaymentError):
    if isinstance(error, InsufficientFundsError):
        # معالجة عدم كفاية الرصيد
    elif isinstance(error, PaymentMethodError):
        # معالجة مشاكل طريقة الدفع
```

## التقارير المالية

### تقرير المبيعات
```python
async def generate_sales_report(
    start_date: date,
    end_date: date,
    service_type: Optional[ServiceType] = None
) -> Report:
    # إنشاء تقرير المبيعات
```

### تقرير الأرباح
```python
async def generate_revenue_report(
    doctor_id: UUID,
    period: ReportPeriod
) -> Report:
    # إنشاء تقرير الأرباح للطبيب
```

## الأمان والامتثال

### تشفير البيانات
- تشفير بيانات البطاقات
- تخزين آمن للمعرف المشفر
- عدم تخزين بيانات حساسة

### الامتثال
- PCI DSS
- GDPR
- متطلبات المحاسبة المحلية

## الاختبارات
```python
class TestPaymentSystem:
    async def test_payment_creation(self):
        # اختبار إنشاء دفعة
        
    async def test_payment_processing(self):
        # اختبار معالجة الدفع
        
    async def test_refund_process(self):
        # اختبار عملية الإرجاع
```

## التكامل مع الأنظمة الأخرى

### نظام المواعيد
```python
async def handle_appointment_payment(appointment_id: UUID):
    # معالجة دفع الموعد
```

### نظام الأدوية
```python
async def handle_medication_payment(order_id: UUID):
    # معالجة دفع الأدوية
```

### نظام الإشعارات
```python
async def notify_payment_status(payment_id: UUID):
    # إرسال إشعارات حالة الدفع
``` 