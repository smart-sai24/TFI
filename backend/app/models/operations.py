from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = 'roles'

    name = Column(String, primary_key=True)
    description = Column(Text, nullable=True)
    users = relationship('User', back_populates='role_profile')


class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),)


class RolePermission(Base):
    __tablename__ = 'role_permissions'

    role_name = Column(String, ForeignKey('roles.name', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)


class Batch(Base):
    __tablename__ = 'batches'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, nullable=False)
    status = Column(String, nullable=False, default='active')
    starts_on = Column(Date, nullable=True)
    ends_on = Column(Date, nullable=True)
    mentor_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    host_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    coordinator_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    students = relationship('Student', back_populates='batch')
    assignments = relationship('Assignment', back_populates='batch')
    attendance_sessions = relationship('AttendanceSession', back_populates='batch')


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False, index=True)
    registration_number = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    domain = Column(String, nullable=False)
    enrollment_status = Column(String, nullable=False, default='active')
    joined_on = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    batch = relationship('Batch', back_populates='students')
    attendance_records = relationship('AttendanceRecord', back_populates='student')
    submissions = relationship('Submission', back_populates='student')
    performance_scores = relationship('PerformanceScore', back_populates='student')
    risk_profile = relationship('RiskProfile', back_populates='student', uselist=False)
    certificates = relationship('Certificate', back_populates='student')
    attendance_predictions = relationship('AttendancePrediction', back_populates='student')
    performance_predictions = relationship('PerformancePrediction', back_populates='student')
    risk_predictions = relationship('RiskPrediction', back_populates='student')
    assignment_evaluations = relationship('AssignmentEvaluation', back_populates='student')
    authenticity_checks = relationship('AssignmentAuthenticityCheck', back_populates='student')


class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    session_date = Column(Date, nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    required_minutes = Column(Integer, nullable=False, default=90)
    source_file = Column(String, nullable=True)
    import_hash = Column(String, nullable=True, index=True)
    created_by_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batch = relationship('Batch', back_populates='attendance_sessions')
    records = relationship('AttendanceRecord', back_populates='session')


class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    join_time = Column(DateTime(timezone=True), nullable=True)
    leave_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=False, default=0)
    attendance_percentage = Column(Float, nullable=False, default=0)
    status = Column(String, nullable=False)
    late_joining = Column(Boolean, nullable=False, default=False)
    early_leaving = Column(Boolean, nullable=False, default=False)
    engagement_score = Column(Float, nullable=False, default=0)
    raw_payload = Column(JSON, nullable=False, default=dict)

    session = relationship('AttendanceSession', back_populates='records')
    student = relationship('Student', back_populates='attendance_records')

    __table_args__ = (
        UniqueConstraint('session_id', 'student_id', name='uq_attendance_record_session_student'),
        Index('ix_attendance_student_session', 'student_id', 'session_id'),
    )


class Assignment(Base):
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assignment_type = Column(String, nullable=False, default='general')
    due_at = Column(DateTime(timezone=True), nullable=False)
    max_score = Column(Float, nullable=False, default=100)
    created_by_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    batch = relationship('Batch', back_populates='assignments')
    submissions = relationship('Submission', back_populates='assignment')


class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default='missing')
    score = Column(Float, nullable=True)
    is_late = Column(Boolean, nullable=False, default=False)
    feedback = Column(Text, nullable=True)
    ai_evaluation = Column(JSON, nullable=False, default=dict)

    assignment = relationship('Assignment', back_populates='submissions')
    student = relationship('Student', back_populates='submissions')
    assignment_evaluations = relationship('AssignmentEvaluation', back_populates='submission')

    __table_args__ = (UniqueConstraint('assignment_id', 'student_id', name='uq_submission_assignment_student'),)


class PerformanceScore(Base):
    __tablename__ = 'performance_scores'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    score_date = Column(Date, nullable=False, index=True)
    attendance_score = Column(Float, nullable=False)
    assignment_score = Column(Float, nullable=False)
    engagement_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    batch_rank = Column(Integer, nullable=True)
    overall_rank = Column(Integer, nullable=True)
    category = Column(String, nullable=False)
    trend = Column(String, nullable=False, default='stable')

    student = relationship('Student', back_populates='performance_scores')

    __table_args__ = (CheckConstraint('overall_score >= 0 AND overall_score <= 100', name='ck_performance_overall_score'),)


class RiskProfile(Base):
    __tablename__ = 'risk_profiles'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), unique=True, nullable=False)
    risk_level = Column(String, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    reasons = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    predicted_completion_probability = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship('Student', back_populates='risk_profile')


class Certificate(Base):
    __tablename__ = 'certificates'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    eligibility_score = Column(Float, nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    certificate_url = Column(String, nullable=True)
    requirements_snapshot = Column(JSON, nullable=False, default=dict)

    student = relationship('Student', back_populates='certificates')


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    recipient_type = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)
    template = Column(String, nullable=False)
    status = Column(String, nullable=False, default='queued')
    payload = Column(JSON, nullable=False, default=dict)
    response_status = Column(String, nullable=False, default='pending', index=True)
    response_payload = Column(JSON, nullable=False, default=dict)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    actor_uid = Column(String, ForeignKey('users.uid'), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    report_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default='queued')
    generated_by_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    file_url = Column(String, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    metrics_snapshot = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AttendancePrediction(Base):
    __tablename__ = 'attendance_predictions'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    prediction_window = Column(String, nullable=False, default='30_days')
    current_attendance = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    forecast = Column(JSON, nullable=False, default=dict)
    reasons = Column(JSON, nullable=False, default=list)
    recommended_action = Column(Text, nullable=True)
    model_version = Column(String, nullable=False, default='heuristic-v1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    student = relationship('Student', back_populates='attendance_predictions')


class PerformancePrediction(Base):
    __tablename__ = 'performance_predictions'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    current_score = Column(Float, nullable=False)
    predicted_final_score = Column(Float, nullable=False)
    predicted_category = Column(String, nullable=False, index=True)
    certificate_probability = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    drivers = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False, default='heuristic-v1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    student = relationship('Student', back_populates='performance_predictions')


class RiskPrediction(Base):
    __tablename__ = 'risk_predictions'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    risk_level = Column(String, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_types = Column(JSON, nullable=False, default=list)
    reasoning = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False, default='heuristic-v1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    student = relationship('Student', back_populates='risk_predictions')


class AiReport(Base):
    __tablename__ = 'ai_reports'

    id = Column(Integer, primary_key=True)
    report_type = Column(String, nullable=False, index=True)
    output_format = Column(String, nullable=False, default='markdown')
    status = Column(String, nullable=False, default='completed', index=True)
    generated_by_uid = Column(String, ForeignKey('users.uid'), nullable=True)
    file_url = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class AiInsight(Base):
    __tablename__ = 'ai_insights'

    id = Column(Integer, primary_key=True)
    audience_role = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    severity = Column(String, nullable=False, default='neutral', index=True)
    source = Column(String, nullable=False, default='insights_engine')
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class AiConversation(Base):
    __tablename__ = 'ai_conversations'

    id = Column(Integer, primary_key=True)
    user_uid = Column(String, ForeignKey('users.uid'), nullable=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class AssignmentEvaluation(Base):
    __tablename__ = 'assignment_evaluations'

    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=True, index=True)
    title = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    grade = Column(String, nullable=False, index=True)
    feedback = Column(Text, nullable=False)
    strengths = Column(JSON, nullable=False, default=list)
    improvements = Column(JSON, nullable=False, default=list)
    risk_flags = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False, default='heuristic-v1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    submission = relationship('Submission', back_populates='assignment_evaluations')
    student = relationship('Student', back_populates='assignment_evaluations')


class AssignmentAuthenticityCheck(Base):
    __tablename__ = 'assignment_authenticity_checks'

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id', ondelete='SET NULL'), nullable=True, index=True)
    submission_id = Column(Integer, ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=True, index=True)
    title = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    ai_generated_risk = Column(Float, nullable=False)
    code_quality_score = Column(Float, nullable=False)
    github_activity_score = Column(Float, nullable=False)
    originality_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String, nullable=False, index=True)
    matched_submission_id = Column(Integer, nullable=True)
    fingerprint = Column(JSON, nullable=False, default=list)
    github_evidence = Column(JSON, nullable=False, default=dict)
    findings = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    model_version = Column(String, nullable=False, default='authenticity-v1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    student = relationship('Student', back_populates='authenticity_checks')
