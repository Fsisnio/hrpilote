export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  status: UserStatus;
  organization_id: number;
  department_id?: number;
  manager_id?: number;
  phone?: string;
  address?: string;
  date_of_birth?: string;
  profile_picture?: string;
  is_email_verified: boolean;
  is_active: boolean;
  last_login?: string;
  failed_login_attempts: number;
  locked_until?: string;
  created_at: string;
  updated_at?: string;
}

export interface Organization {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: OrganizationStatus;
  email?: string;
  phone?: string;
  website?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  industry?: string;
  size?: string;
  founded_year?: number;
  tax_id?: string;
  timezone?: string;
  currency?: string;
  language?: string;
  enable_attendance: boolean;
  enable_leave_management: boolean;
  enable_payroll: boolean;
  enable_training: boolean;
  enable_expenses: boolean;
  enable_documents: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: DepartmentStatus;
  organization_id: number;
  parent_department_id?: number;
  budget?: number;
  location?: string;
  contact_email?: string;
  contact_phone?: string;
  max_employees?: number;
  allow_remote_work: boolean;
  working_hours_start?: string;
  working_hours_end?: string;
  created_at: string;
  updated_at?: string;
}

export interface Employee {
  id: number;
  employee_id: string;
  user_id: number;
  organization_id: number;
  department_id?: number;
  first_name: string;
  last_name: string;
  middle_name?: string;
  date_of_birth?: string;
  gender?: Gender;
  nationality?: string;
  marital_status?: string;
  personal_email?: string;
  personal_phone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  status: EmployeeStatus;
  employment_type: EmploymentType;
  position: string;
  job_title: string;
  hire_date: string;
  termination_date?: string;
  probation_end_date?: string;
  base_salary?: number;
  hourly_rate?: number;
  currency?: string;
  working_hours_per_week?: number;
  work_schedule?: string;
  timezone?: string;
  benefits_package?: string;
  insurance_provider?: string;
  insurance_policy_number?: string;
  id_document_type?: string;
  id_document_number?: string;
  id_document_expiry?: string;
  hr_manager_id?: number;
  direct_manager_id?: number;
  hr_notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

// Enums
export enum UserRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  ORG_ADMIN = 'ORG_ADMIN',
  HR = 'HR',
  MANAGER = 'MANAGER',
  DIRECTOR = 'DIRECTOR',
  PAYROLL = 'PAYROLL',
  EMPLOYEE = 'EMPLOYEE',
}

export enum UserStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
  PENDING = 'PENDING',
}

export enum OrganizationStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
  PENDING = 'PENDING',
}

export enum DepartmentStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
}

export enum EmployeeStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  TERMINATED = 'TERMINATED',
  ON_LEAVE = 'ON_LEAVE',
  PROBATION = 'PROBATION',
}

export enum EmploymentType {
  FULL_TIME = 'FULL_TIME',
  PART_TIME = 'PART_TIME',
  CONTRACT = 'CONTRACT',
  INTERN = 'INTERN',
  FREELANCE = 'FREELANCE',
}

export enum Gender {
  MALE = 'MALE',
  FEMALE = 'FEMALE',
  OTHER = 'OTHER',
  PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY',
} 