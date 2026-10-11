from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


# User schemas
class UserBase(BaseModel):
    email: str = Field(min_length=3)
    full_name: str
    modules: List[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    modules: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    """Cambio de contraseña por AdminPRO. La clave viaja solo en el request;
    nunca se devuelve ni se registra en logs."""

    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Employee schemas
class EmployeeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    department: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MergeRequest(BaseModel):
    """Fusionar empleados duplicados: reasigna registros al conservado
    y desactiva los demás. Los IDs duplicados no deben incluir al conservado."""

    keep_id: int
    duplicate_ids: List[int] = Field(min_length=1)


class DuplicateMember(BaseModel):
    id: int
    name: str
    department: Optional[str] = None
    is_active: bool


class DuplicateGroup(BaseModel):
    key: str
    employees: List[DuplicateMember]


class MergeResult(BaseModel):
    keep_id: int
    deactivated_ids: List[int]
    moved_attendances: int
    moved_justifications: int


# Department schemas
class DepartmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Attendance schemas
class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    total_hours: Optional[str] = None
    source: str = "biometric"


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    total_hours: Optional[str] = None
    justification_id: Optional[int] = None


class AttendanceResponse(AttendanceBase):
    id: int
    created_at: datetime
    justification_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# Justification schemas
class JustificationBase(BaseModel):
    employee_id: int
    type: str = Field(pattern="^(permiso|licencia_medica|vacaciones|otro)$")
    description: Optional[str] = None
    start_date: date
    end_date: date


class JustificationCreate(JustificationBase):
    pass


class JustificationUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class JustificationResponse(JustificationBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Visitor schemas
class VisitorBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    document_number: str = Field(min_length=1, max_length=50)
    visited_person: Optional[str] = Field(default=None, max_length=255)
    institution: Optional[str] = Field(default=None, max_length=255)
    visit_justification: Optional[str] = None


class VisitorCreate(VisitorBase):
    pass


class VisitorResponse(VisitorBase):
    id: int
    is_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VisitorQRResponse(BaseModel):
    qr_base64: str
    visitor: VisitorResponse


# Audit log schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Excel import schemas
class ExcelImportResult(BaseModel):
    processed: int
    created: int
    updated: int
    errors: List[str] = Field(default_factory=list)


# Statistics schemas
class AttendanceStats(BaseModel):
    total_employees: int
    present_today: int
    absent_today: int
    late_today: int
    total_hours: float


class AttendanceChartData(BaseModel):
    date: date
    present: int
    absent: int
    late: int


# Pagination
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# Report QR schemas
class ReportQRRequest(BaseModel):
    employee_id: Optional[int] = None
    department: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReportQRResponse(BaseModel):
    qr_base64: str
    url: str
