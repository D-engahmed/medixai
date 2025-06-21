# نظام المحادثات الطبية

## نظرة عامة
نظام المحادثات الطبية يوفر واجهة ذكية للتواصل مع المرضى، باستخدام نموذج BioMedX2 للإجابة على الاستفسارات الطبية ونموذج منفصل للمحادثات العامة.

## هيكل النظام

### المكونات الرئيسية
```
app/
├── models/
│   ├── chat.py             # نموذج المحادثة
│   └── message.py          # نموذج الرسائل
├── schemas/
│   └── chat.py            # مخططات المحادثة
├── api/v1/
│   └── chat.py            # نقاط نهاية المحادثة
├── services/
│   ├── chat_service.py    # خدمات المحادثة
│   ├── rag_service.py     # خدمة RAG
│   └── ml_service.py      # خدمات الذكاء الاصطناعي
└── utils/
    └── text_processor.py  # معالجة النصوص
```

## نماذج البيانات

### نموذج المحادثة
```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID, primary_key=True)
    patient_id = Column(UUID, ForeignKey("patients.id"))
    session_type = Column(Enum(ChatType))
    status = Column(Enum(SessionStatus))
    context = Column(JSONB)
    metadata = Column(JSONB)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # العلاقات
    patient = relationship("Patient", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
```

### نموذج الرسائل
```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID, primary_key=True)
    session_id = Column(UUID, ForeignKey("chat_sessions.id"))
    sender_type = Column(Enum(SenderType))
    content = Column(Text)
    embedding = Column(Vector(384))  # للبحث الدلالي
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    session = relationship("ChatSession", back_populates="messages")
```

## خدمات النظام

### خدمة المحادثة
```python
class ChatService:
    async def create_session(
        self,
        patient_id: UUID,
        session_type: ChatType
    ) -> ChatSession:
        """إنشاء جلسة محادثة جديدة"""
        
    async def process_message(
        self,
        session_id: UUID,
        content: str
    ) -> ChatResponse:
        """معالجة رسالة المستخدم"""
        
    async def handle_escalation(
        self,
        session_id: UUID,
        reason: str
    ) -> EscalationResult:
        """معالجة تصعيد المحادثة"""
```

### خدمة RAG
```python
class RAGService:
    async def process_medical_query(
        self,
        query: str,
        context: Dict
    ) -> RAGResponse:
        """معالجة الاستفسار الطبي باستخدام RAG"""
        
    async def retrieve_relevant_docs(
        self,
        query: str
    ) -> List[Document]:
        """استرجاع الوثائق ذات الصلة"""
```

## نماذج الذكاء الاصطناعي

### نموذج BioMedX2
```python
class BioMedX2Model:
    def __init__(self):
        """تهيئة النموذج الطبي المصغر"""
        
    async def generate_response(
        self,
        query: str,
        context: List[Document]
    ) -> str:
        """توليد إجابة طبية"""
```

### نموذج المحادثة العامة
```python
class GeneralChatModel:
    async def generate_response(
        self,
        message: str,
        history: List[Message]
    ) -> str:
        """توليد إجابة للمحادثة العامة"""
```

## تدفقات العمل

### معالجة الرسائل
1. تصنيف نوع الرسالة
2. اختيار النموذج المناسب
3. استرجاع السياق
4. توليد الإجابة
5. تحليل الحاجة للتصعيد

### التصعيد التلقائي
1. تحديد سبب التصعيد
2. إنشاء حالة تصعيد
3. توجيه المريض
4. إخطار الطبيب
5. متابعة الحالة

## معالجة النصوص

### تحليل النص
```python
class TextAnalyzer:
    async def analyze_medical_terms(
        self,
        text: str
    ) -> List[MedicalTerm]:
        """تحليل المصطلحات الطبية"""
        
    async def detect_urgency(
        self,
        text: str
    ) -> UrgencyLevel:
        """تحديد مستوى الإلحاح"""
```

### معالجة السياق
```python
class ContextProcessor:
    async def extract_symptoms(
        self,
        text: str
    ) -> List[Symptom]:
        """استخراج الأعراض"""
        
    async def build_medical_context(
        self,
        patient_id: UUID,
        current_text: str
    ) -> Context:
        """بناء السياق الطبي"""
```

## التكامل مع الأنظمة الأخرى

### نظام المواعيد
```python
async def create_appointment_from_chat(
    session_id: UUID,
    doctor_specialty: str
) -> Appointment:
    """إنشاء موعد من المحادثة"""
```

### نظام الأدوية
```python
async def create_medication_order(
    session_id: UUID,
    medication_suggestion: str
) -> Order:
    """إنشاء طلب دواء"""
```

## المراقبة والتحليل

### تحليل المحادثات
```python
class ChatAnalytics:
    async def analyze_session(
        self,
        session_id: UUID
    ) -> SessionAnalysis:
        """تحليل جلسة محادثة"""
        
    async def generate_insights(
        self,
        patient_id: UUID
    ) -> List[Insight]:
        """توليد رؤى من المحادثات"""
```

### مراقبة الأداء
```python
class PerformanceMonitor:
    async def track_response_time(
        self,
        session_id: UUID,
        response_time: float
    ) -> None:
        """تتبع زمن الاستجابة"""
        
    async def monitor_model_accuracy(
        self,
        model_type: str,
        prediction: str,
        feedback: str
    ) -> None:
        """مراقبة دقة النموذج"""
```

## الاختبارات

### اختبارات الوحدة
```python
class TestChatSystem:
    async def test_message_processing(self):
        """اختبار معالجة الرسائل"""
        
    async def test_escalation_logic(self):
        """اختبار منطق التصعيد"""
```

### اختبارات التكامل
```python
class TestChatIntegration:
    async def test_rag_system(self):
        """اختبار نظام RAG"""
        
    async def test_model_switching(self):
        """اختبار تبديل النماذج"""
```

## واجهة المستخدم

### واجهة المحادثة
```typescript
interface ChatInterface {
    sessionId: string;
    messages: Message[];
    status: SessionStatus;
    suggestions: string[];
    escalationOptions: EscalationOption[];
}
```

### لوحة التحكم
```typescript
interface ChatDashboard {
    activeSessions: number;
    averageResponseTime: number;
    escalationRate: number;
    satisfactionScore: number;
    popularTopics: Topic[];
}
``` 