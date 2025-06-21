"""
Follow-Up System Service
"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status

from app.models.follow_up import (
    Interaction,
    FollowUpRule,
    HealthMetric,
    TreatmentPlan
)
from app.schemas.follow_up import (
    InteractionCreate,
    InteractionUpdate,
    Timeline,
    TimelineEntry,
    AnalyticsFilter,
    AnalyticsSummary,
    PatientSummary,
    DoctorSummary,
    InteractionType
)

def create_interaction(db: Session, interaction: InteractionCreate) -> Interaction:
    """إنشاء تفاعل جديد"""
    db_interaction = Interaction(
        type=interaction.type,
        title=interaction.title,
        description=interaction.description,
        metadata=interaction.metadata,
        timestamp=interaction.timestamp,
        status=interaction.status,
        importance=interaction.importance,
        requires_action=interaction.requires_action,
        action_by=interaction.action_by,
        patient_id=interaction.patient_id,
        doctor_id=interaction.doctor_id,
        reference_id=interaction.reference_id,
        reference_type=interaction.reference_type
    )
    
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    # تطبيق قواعد المتابعة
    apply_follow_up_rules(db, db_interaction)
    
    return db_interaction

def update_interaction(
    db: Session,
    interaction_id: UUID,
    update_data: InteractionUpdate
) -> Interaction:
    """تحديث تفاعل"""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التفاعل غير موجود"
        )
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(interaction, field, value)
    
    db.commit()
    db.refresh(interaction)
    return interaction

def get_patient_timeline(
    db: Session,
    patient_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    interaction_types: Optional[List[str]] = None
) -> Timeline:
    """الحصول على الجدول الزمني للمريض"""
    query = db.query(Interaction).filter(Interaction.patient_id == patient_id)
    
    if start_date:
        query = query.filter(Interaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Interaction.timestamp <= end_date)
    if interaction_types:
        query = query.filter(Interaction.type.in_(interaction_types))
    
    query = query.order_by(desc(Interaction.timestamp))
    interactions = query.all()
    
    # تجميع التفاعلات حسب اليوم
    timeline_entries = []
    current_date = None
    current_interactions = []
    
    for interaction in interactions:
        interaction_date = interaction.timestamp.date()
        
        if current_date != interaction_date and current_interactions:
            timeline_entries.append(
                TimelineEntry(
                    date=datetime.combine(current_date, datetime.min.time()),
                    interactions=current_interactions.copy(),
                    summary=generate_day_summary(current_interactions),
                    total_items=len(current_interactions),
                    has_critical=any(i.importance >= 4 for i in current_interactions)
                )
            )
            current_interactions = []
        
        current_date = interaction_date
        current_interactions.append(interaction)
    
    # إضافة آخر مجموعة
    if current_interactions:
        timeline_entries.append(
            TimelineEntry(
                date=datetime.combine(current_date, datetime.min.time()),
                interactions=current_interactions,
                summary=generate_day_summary(current_interactions),
                total_items=len(current_interactions),
                has_critical=any(i.importance >= 4 for i in current_interactions)
            )
        )
    
    return Timeline(
        entries=timeline_entries,
        total_interactions=len(interactions),
        date_range={
            "start": start_date or interactions[-1].timestamp if interactions else None,
            "end": end_date or interactions[0].timestamp if interactions else None
        },
        statistics=generate_timeline_statistics(interactions)
    )

def get_analytics_summary(
    db: Session,
    patient_id: Optional[UUID] = None,
    doctor_id: Optional[UUID] = None,
    filters: Optional[AnalyticsFilter] = None
) -> AnalyticsSummary:
    """الحصول على ملخص التحليلات"""
    query = db.query(Interaction)
    
    if patient_id:
        query = query.filter(Interaction.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Interaction.doctor_id == doctor_id)
    
    if filters:
        query = query.filter(
            and_(
                Interaction.timestamp >= filters.start_date,
                Interaction.timestamp <= filters.end_date
            )
        )
        if filters.interaction_types:
            query = query.filter(Interaction.type.in_(filters.interaction_types))
    
    interactions = query.all()
    
    # حساب الإحصائيات
    total = len(interactions)
    type_counts = {}
    importance_sum = 0
    completed = 0
    response_times = {}
    
    for interaction in interactions:
        # عدد التفاعلات حسب النوع
        type_counts[interaction.type] = type_counts.get(interaction.type, 0) + 1
        
        # متوسط الأهمية
        importance_sum += interaction.importance
        
        # معدل الإكمال
        if interaction.status == "completed":
            completed += 1
        
        # وقت الاستجابة
        if interaction.requires_action and interaction.action_by:
            response_time = (interaction.action_by - interaction.timestamp).total_seconds() / 3600
            if interaction.type not in response_times:
                response_times[interaction.type] = []
            response_times[interaction.type].append(response_time)
    
    # حساب المتوسطات
    avg_importance = importance_sum / total if total > 0 else 0
    completion_rate = (completed / total * 100) if total > 0 else 0
    avg_response_times = {
        k: sum(v) / len(v) for k, v in response_times.items()
    }
    
    # تحليل الاتجاهات
    trends = analyze_trends(interactions, filters.period if filters else "monthly")
    
    # تحليل الأنماط الشائعة
    patterns = analyze_patterns(interactions) if filters and filters.include_metadata else []
    
    return AnalyticsSummary(
        total_interactions=total,
        interaction_types_count=type_counts,
        average_importance=avg_importance,
        completion_rate=completion_rate,
        response_times=avg_response_times,
        trends=trends,
        common_patterns=patterns
    )

def get_patient_summary(db: Session, patient_id: UUID) -> PatientSummary:
    """الحصول على ملخص المريض"""
    # الحصول على المواعيد
    appointments = db.query(Interaction).filter(
        and_(
            Interaction.patient_id == patient_id,
            Interaction.type == InteractionType.APPOINTMENT
        )
    ).order_by(desc(Interaction.timestamp)).all()
    
    # الحصول على الوصفات الطبية النشطة
    active_prescriptions = db.query(Interaction).filter(
        and_(
            Interaction.patient_id == patient_id,
            Interaction.type == InteractionType.PRESCRIPTION,
            Interaction.status == "active"
        )
    ).count()
    
    # حساب معدل الالتزام
    total_required = db.query(Interaction).filter(
        and_(
            Interaction.patient_id == patient_id,
            Interaction.requires_action == True
        )
    ).count()
    
    completed_required = db.query(Interaction).filter(
        and_(
            Interaction.patient_id == patient_id,
            Interaction.requires_action == True,
            Interaction.status == "completed"
        )
    ).count()
    
    compliance_rate = (completed_required / total_required * 100) if total_required > 0 else 0
    
    # تحليل عوامل الخطر
    risk_factors = analyze_risk_factors(db, patient_id)
    
    # الحصول على التفاعلات الأخيرة
    recent_interactions = db.query(Interaction).filter(
        Interaction.patient_id == patient_id
    ).order_by(desc(Interaction.timestamp)).limit(5).all()
    
    # تحليل الاتجاهات الصحية
    health_trends = analyze_health_trends(db, patient_id)
    
    return PatientSummary(
        total_visits=len(appointments),
        last_visit=appointments[0].timestamp if appointments else None,
        upcoming_appointments=len([a for a in appointments if a.timestamp > datetime.now()]),
        active_prescriptions=active_prescriptions,
        compliance_rate=compliance_rate,
        risk_factors=risk_factors,
        recent_interactions=recent_interactions,
        health_trends=health_trends
    )

def get_doctor_summary(db: Session, doctor_id: UUID) -> DoctorSummary:
    """الحصول على ملخص الطبيب"""
    # عدد المرضى الكلي
    total_patients = db.query(Interaction.patient_id).filter(
        Interaction.doctor_id == doctor_id
    ).distinct().count()
    
    # الحالات النشطة
    active_cases = db.query(TreatmentPlan).filter(
        and_(
            TreatmentPlan.doctor_id == doctor_id,
            TreatmentPlan.status == "active"
        )
    ).count()
    
    # معدل المتابعة
    follow_ups = db.query(Interaction).filter(
        and_(
            Interaction.doctor_id == doctor_id,
            Interaction.type == InteractionType.FOLLOW_UP
        )
    ).count()
    
    total_appointments = db.query(Interaction).filter(
        and_(
            Interaction.doctor_id == doctor_id,
            Interaction.type == InteractionType.APPOINTMENT
        )
    ).count()
    
    follow_up_rate = (follow_ups / total_appointments * 100) if total_appointments > 0 else 0
    
    # متوسط الفترة بين الزيارات
    visit_intervals = calculate_visit_intervals(db, doctor_id)
    
    # نتائج العلاج
    treatment_outcomes = analyze_treatment_outcomes(db, doctor_id)
    
    # رضا المرضى
    satisfaction = calculate_patient_satisfaction(db, doctor_id)
    
    # توزيع العمل
    workload = analyze_workload_distribution(db, doctor_id)
    
    return DoctorSummary(
        total_patients=total_patients,
        active_cases=active_cases,
        follow_up_rate=follow_up_rate,
        average_visit_interval=visit_intervals,
        treatment_outcomes=treatment_outcomes,
        patient_satisfaction=satisfaction,
        workload_distribution=workload
    )

# Helper Functions

def apply_follow_up_rules(db: Session, interaction: Interaction) -> None:
    """تطبيق قواعد المتابعة"""
    rules = db.query(FollowUpRule).filter(
        and_(
            FollowUpRule.trigger_type == interaction.type,
            FollowUpRule.is_active == True
        )
    ).order_by(FollowUpRule.priority).all()
    
    for rule in rules:
        if evaluate_rule_conditions(interaction, rule.conditions):
            execute_rule_actions(db, interaction, rule.actions)

def generate_day_summary(interactions: List[Interaction]) -> str:
    """توليد ملخص لليوم"""
    summary_parts = []
    
    type_counts = {}
    for interaction in interactions:
        type_counts[interaction.type] = type_counts.get(interaction.type, 0) + 1
    
    for type_name, count in type_counts.items():
        summary_parts.append(f"{count} {type_name}")
    
    critical_count = sum(1 for i in interactions if i.importance >= 4)
    if critical_count:
        summary_parts.append(f"{critical_count} حالات هامة")
    
    return "، ".join(summary_parts)

def generate_timeline_statistics(interactions: List[Interaction]) -> Dict[str, Any]:
    """توليد إحصائيات الجدول الزمني"""
    return {
        "total_by_type": {
            type_name: len([i for i in interactions if i.type == type_name])
            for type_name in set(i.type for i in interactions)
        },
        "importance_distribution": {
            str(importance): len([i for i in interactions if i.importance == importance])
            for importance in range(1, 6)
        },
        "completion_rate": len([i for i in interactions if i.status == "completed"]) / len(interactions) * 100
        if interactions else 0
    }

def analyze_trends(
    interactions: List[Interaction],
    period: str
) -> Dict[str, List[float]]:
    """تحليل الاتجاهات"""
    trends = {
        "interaction_count": [],
        "importance_avg": [],
        "completion_rate": []
    }
    
    # تجميع التفاعلات حسب الفترة
    period_groups = group_by_period(interactions, period)
    
    for group in period_groups:
        if group:
            trends["interaction_count"].append(len(group))
            trends["importance_avg"].append(
                sum(i.importance for i in group) / len(group)
            )
            trends["completion_rate"].append(
                len([i for i in group if i.status == "completed"]) / len(group) * 100
            )
        else:
            trends["interaction_count"].append(0)
            trends["importance_avg"].append(0)
            trends["completion_rate"].append(0)
    
    return trends

def analyze_patterns(interactions: List[Interaction]) -> List[Dict[str, Any]]:
    """تحليل الأنماط الشائعة"""
    patterns = []
    
    # تحليل تسلسل التفاعلات
    sequence_patterns = find_sequence_patterns(interactions)
    if sequence_patterns:
        patterns.extend(sequence_patterns)
    
    # تحليل العلاقات بين الأنواع
    type_correlations = find_type_correlations(interactions)
    if type_correlations:
        patterns.extend(type_correlations)
    
    # تحليل أنماط الوقت
    time_patterns = find_time_patterns(interactions)
    if time_patterns:
        patterns.extend(time_patterns)
    
    return patterns

def analyze_risk_factors(db: Session, patient_id: UUID) -> List[str]:
    """تحليل عوامل الخطر"""
    risk_factors = []
    
    # تحليل التفاعلات الهامة
    critical_interactions = db.query(Interaction).filter(
        and_(
            Interaction.patient_id == patient_id,
            Interaction.importance >= 4
        )
    ).order_by(desc(Interaction.timestamp)).limit(10).all()
    
    if critical_interactions:
        risk_factors.append("تفاعلات حرجة متكررة")
    
    # تحليل معدل الالتزام
    compliance_rate = calculate_compliance_rate(db, patient_id)
    if compliance_rate < 70:
        risk_factors.append("معدل التزام منخفض")
    
    # تحليل المقاييس الصحية
    health_metrics = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id
    ).order_by(desc(HealthMetric.timestamp)).all()
    
    abnormal_metrics = analyze_health_metrics(health_metrics)
    risk_factors.extend(abnormal_metrics)
    
    return risk_factors

def analyze_health_trends(db: Session, patient_id: UUID) -> Dict[str, List[float]]:
    """تحليل الاتجاهات الصحية"""
    trends = {}
    
    # الحصول على المقاييس الصحية
    metrics = db.query(HealthMetric).filter(
        HealthMetric.patient_id == patient_id
    ).order_by(HealthMetric.timestamp).all()
    
    # تجميع المقاييس حسب النوع
    metric_groups = {}
    for metric in metrics:
        if metric.metric_type not in metric_groups:
            metric_groups[metric.metric_type] = []
        metric_groups[metric.metric_type].append(metric)
    
    # حساب الاتجاهات لكل نوع
    for metric_type, group in metric_groups.items():
        values = []
        for metric in group:
            if isinstance(metric.value, dict) and "value" in metric.value:
                values.append(float(metric.value["value"]))
            elif isinstance(metric.value, (int, float)):
                values.append(float(metric.value))
        
        if values:
            trends[metric_type] = values
    
    return trends

def calculate_visit_intervals(db: Session, doctor_id: UUID) -> float:
    """حساب متوسط الفترة بين الزيارات"""
    appointments = db.query(Interaction).filter(
        and_(
            Interaction.doctor_id == doctor_id,
            Interaction.type == InteractionType.APPOINTMENT,
            Interaction.status == "completed"
        )
    ).order_by(Interaction.timestamp).all()
    
    if len(appointments) < 2:
        return 0
    
    intervals = []
    for i in range(1, len(appointments)):
        interval = (appointments[i].timestamp - appointments[i-1].timestamp).days
        intervals.append(interval)
    
    return sum(intervals) / len(intervals)

def analyze_treatment_outcomes(db: Session, doctor_id: UUID) -> Dict[str, float]:
    """تحليل نتائج العلاج"""
    treatment_plans = db.query(TreatmentPlan).filter(
        and_(
            TreatmentPlan.doctor_id == doctor_id,
            TreatmentPlan.status.in_(["completed", "failed"])
        )
    ).all()
    
    outcomes = {
        "success_rate": 0,
        "avg_duration": 0,
        "goal_completion": 0
    }
    
    if not treatment_plans:
        return outcomes
    
    successful = len([p for p in treatment_plans if p.status == "completed"])
    outcomes["success_rate"] = (successful / len(treatment_plans)) * 100
    
    durations = []
    goal_completions = []
    
    for plan in treatment_plans:
        if plan.end_date and plan.start_date:
            duration = (plan.end_date - plan.start_date).days
            durations.append(duration)
        
        if plan.goals and plan.progress:
            completed_goals = sum(1 for g in plan.progress.values() if g.get("completed", False))
            goal_completions.append(completed_goals / len(plan.goals) * 100)
    
    if durations:
        outcomes["avg_duration"] = sum(durations) / len(durations)
    
    if goal_completions:
        outcomes["goal_completion"] = sum(goal_completions) / len(goal_completions)
    
    return outcomes

def calculate_patient_satisfaction(db: Session, doctor_id: UUID) -> float:
    """حساب رضا المرضى"""
    interactions = db.query(Interaction).filter(
        and_(
            Interaction.doctor_id == doctor_id,
            Interaction.type.in_([InteractionType.APPOINTMENT, InteractionType.FOLLOW_UP]),
            Interaction.metadata.has_key("satisfaction_rating")
        )
    ).all()
    
    if not interactions:
        return 0
    
    ratings = []
    for interaction in interactions:
        rating = interaction.metadata.get("satisfaction_rating")
        if isinstance(rating, (int, float)):
            ratings.append(float(rating))
    
    return sum(ratings) / len(ratings) if ratings else 0

def analyze_workload_distribution(db: Session, doctor_id: UUID) -> Dict[str, int]:
    """تحليل توزيع العمل"""
    # الحصول على التفاعلات في الشهر الحالي
    start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    interactions = db.query(Interaction).filter(
        and_(
            Interaction.doctor_id == doctor_id,
            Interaction.timestamp >= start_date
        )
    ).all()
    
    distribution = {
        "appointments": 0,
        "follow_ups": 0,
        "prescriptions": 0,
        "chat_sessions": 0,
        "reports": 0
    }
    
    for interaction in interactions:
        if interaction.type in distribution:
            distribution[interaction.type] += 1
    
    return distribution 