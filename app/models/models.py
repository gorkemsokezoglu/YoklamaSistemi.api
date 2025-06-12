from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Date, CheckConstraint, LargeBinary, Integer, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    verifiedEmail = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'academician', 'student'])),
    )

    # İlişkiler
    academician = relationship("Academician", back_populates="user", uselist=False, cascade="all, delete")
    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete")

class Student(Base):
    __tablename__ = "students"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    faculty = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    student_number = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    class_ = Column("class", String(50), nullable=False)  # "class" kelimesi Python'da reserved word olduğu için class_ kullanıyoruz

    __table_args__ = (
        CheckConstraint(
            "student_number ~ '^S[0-9]{8}$'",
            name="check_student_number_format"
        ),
    )

    # İlişkiler
    user = relationship("User", back_populates="student")
    courses = relationship("Course", secondary="course_selections_student", back_populates="students", viewonly=True)
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    face_data = relationship("FaceData", back_populates="student")
    course_selections_student = relationship("CourseSelectionStudent", back_populates="student", cascade="all, delete-orphan")
    performance_records = relationship("PerformanceRecord", back_populates="student", cascade="all, delete-orphan")

class Academician(Base):
    __tablename__ = "academicians"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    faculty = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    academician_number = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "academician_number ~ '^A[0-9]{6}$'",
            name="check_academician_number_format"
        ),
    )

    # İlişkiler
    user = relationship("User", back_populates="academician")
    courses = relationship("Course", back_populates="academician")
    course_selections_academician = relationship("CourseSelectionAcademician", back_populates="academician")

class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    academician_id = Column(UUID(as_uuid=True), ForeignKey("academicians.user_id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    attendances_rate_limit = Column(Float, nullable=True)

    # İlişkiler
    academician = relationship("Academician", back_populates="courses")
    course_selections_student = relationship("CourseSelectionStudent", back_populates="course")
    students = relationship("Student", secondary="course_selections_student", back_populates="courses", viewonly=True)
    attendances = relationship("Attendance", back_populates="course")
    performance_records = relationship("PerformanceRecord", back_populates="course")
    course_selections_academician = relationship("CourseSelectionAcademician", back_populates="course")
    schedules = relationship("CourseSchedule", back_populates="course", cascade="all, delete-orphan")

class CourseSelectionStudent(Base):
    __tablename__ = "course_selections_student"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id", ondelete="CASCADE"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    is_approved = Column(Boolean, nullable=True, default=None)
    created_at = Column(DateTime, server_default=func.now())

    # İlişkiler
    student = relationship("Student", back_populates="course_selections_student")
    course = relationship("Course", back_populates="course_selections_student")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id", ondelete="CASCADE"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    status = Column(Boolean, nullable=True)

    # İlişkiler
    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")

class FaceData(Base):
    __tablename__ = "face_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id", ondelete="CASCADE"))
    face_image = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # İlişkiler
    student = relationship("Student", back_populates="face_data")

class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id", ondelete="CASCADE"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    attendance_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint('attendance_rate >= 0 AND attendance_rate <= 1'),
    )

    # İlişkiler
    student = relationship("Student", back_populates="performance_records")
    course = relationship("Course", back_populates="performance_records")

class CourseSelectionAcademician(Base):
    __tablename__ = "course_selections_academicians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academician_id = Column(UUID(as_uuid=True), ForeignKey("academicians.user_id", ondelete="CASCADE"))
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    is_approved = Column(Boolean, nullable=True, default=None)
    requested_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime, nullable=True)

    # İlişkiler
    academician = relationship("Academician", back_populates="course_selections_academician")
    course = relationship("Course", back_populates="course_selections_academician")

class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    
    # İlişkiler
    departments = relationship("Department", back_populates="faculty", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False)
    
    # İlişkiler
    faculty = relationship("Faculty", back_populates="departments")

    __table_args__ = (
        UniqueConstraint('name', 'faculty_id', name='departments_name_faculty_id_key'),
    )

class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # İlişkiler
    course = relationship("Course", back_populates="schedules")

    __table_args__ = (
        CheckConstraint(
            "weekday IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')"
        ),
    )



