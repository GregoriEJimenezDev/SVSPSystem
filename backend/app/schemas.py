from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ---- Auth schemas ----
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Employee schemas ----
class EmployeeCreate(BaseModel):
    name: str
    department: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    name: str
    department: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Attendance schemas ----
class AttendanceCreate(BaseModel):
    employee_id: int


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    check_in: datetime
    check_out: Optional[datetime]
    total_hours: Optional[str]
    date: datetime
    justification: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Justification schemas ----
# Justification types as constants (not Pydantic enum to avoid schema generation issues)
JUSTIFICATION_PERMISO = "permiso"
JUSTIFICATION_LICENCIA = "licencia"
JUSTIFICATION_VACACIONES = "vacaciones"
JUSTIFICATION_OTRO = "otro"


class JustificationCreate(BaseModel):
    employee_id: int
    type: str  # 'permiso', 'licencia', 'vacaciones', 'otro'
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime


class JustificationUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class JustificationResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    type: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Visitor schemas ----
class VisitorCreate(BaseModel):
    name: str
    last_name: str
    cedula: str


class VisitorUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    cedula: Optional[str] = None


class VisitorResponse(BaseModel):
    id: int
    name: str
    last_name: str
    cedula: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ---- Report/Export schemas ----
class AttendanceSummary(BaseModel):
    employee_id: int
    employee_name: str
    department: Optional[str]
    total_present: int
    total_absent: int
    total_late: int
    period_start: datetime
    period_end: datetime


class QRCodeData(BaseModel):
    report_url: str
    visitor_id: Optional[int] = None
    employee_id: Optional[int] = None


# ---- Role/Permission schemas ----
class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: int
    name: str
    is_system: bool
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True