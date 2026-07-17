export type HealthResponse = {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
  service: string;
  version: string;
  checked_at: string;
};

export type UserProfile = {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserProfile;
};

export type ClinicSession = {
  id: string;
  name: string;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  location: string;
  owner: string;
  notes: string;
  status: "DRAFT" | "ACTIVE" | "ENDED" | "ARCHIVED";
};

export type Patient = {
  id: string;
  case_number: string;
  name: string;
  sex: string;
  birth_date: string | null;
  phone: string;
  residence_area: string;
  emergency_contact: string;
  emergency_contact_phone: string;
  primary_language: string;
  assistance_needs: string;
  is_active: boolean;
};

export type Visit = {
  id: string;
  clinic_session_id: string;
  patient_id: string;
  queue_number: number;
  registered_at: string;
  status: string;
  registration_staff: string;
  notes: string;
  completed_at: string | null;
};

export type ClinicQueueItem = {
  visit_id: string;
  clinic_session_id: string;
  clinic_session_name: string;
  session_date: string;
  patient_id: string;
  patient_case_number: string;
  patient_name: string;
  patient_sex: string;
  queue_number: number;
  status: Visit["status"];
  registered_at: string;
  notes: string;
  latest_vital_sign_at: string | null;
  has_consultation: boolean;
};

export type VitalSign = {
  id: string;
  visit_id: string;
  systolic_blood_pressure: number | null;
  diastolic_blood_pressure: number | null;
  pulse: number | null;
  temperature: string | null;
  oxygen_saturation: number | null;
  height_cm: string | null;
  weight_kg: string | null;
  bmi: string | null;
  blood_glucose: string | null;
  blood_glucose_context: "fasting" | "before_meal" | "after_meal" | "random" | "unknown" | null;
  notes: string;
  measured_by: string;
  measured_at: string;
  created_at: string;
  updated_at: string;
};

export type Consultation = {
  id: string;
  visit_id: string;
  chief_complaint: string;
  symptom_description: string;
  symptom_location: string;
  symptom_onset: string;
  symptom_duration: string;
  symptom_frequency: string;
  symptom_severity: string;
  worsening: string;
  previously_sought_care: string;
  previous_treatment: string;
  student_notes: string;
  recorded_by: string | null;
  recorded_at: string | null;
  clinical_findings: string;
  assessment_summary: string;
  treatment_recommendation: string;
  health_education: string;
  referral_recommendation: string;
  referral_urgency: string;
  follow_up_recommendation: string;
  requires_pharmacy: boolean;
  clinician_notes: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  inspection: string;
  auscultation_olfaction: string;
  inquiry: string;
  palpation: string;
  tongue_notes: string;
  pulse_notes: string;
  created_at: string;
  updated_at: string;
};

export type Medication = {
  id: string;
  code: string;
  name: string;
  generic_name: string;
  brand_name: string;
  dosage_form: string;
  strength: string;
  unit: string;
  route: string;
  manufacturer: string;
  notes: string;
  warnings: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PrescriptionStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "SENT_TO_PHARMACY"
  | "DISPENSING"
  | "WAITING_FOR_VERIFICATION"
  | "VERIFIED"
  | "WAITING_FOR_PICKUP"
  | "DISPENSED"
  | "RETURNED_TO_CLINIC"
  | "VOIDED";

export type PrescriptionItem = {
  id: string;
  prescription_id: string;
  medication_id: string;
  medication: Medication;
  dose: string;
  dose_unit: string;
  frequency: string;
  route: string;
  duration_days: number | null;
  quantity: string;
  instructions: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type Prescription = {
  id: string;
  visit_id: string;
  status: PrescriptionStatus;
  version: number;
  created_by: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  sent_to_pharmacy_at: string | null;
  returned_at: string | null;
  returned_reason: string;
  voided_at: string | null;
  void_reason: string;
  items: PrescriptionItem[];
  created_at: string;
  updated_at: string;
};

export type MedicationPayload = Omit<Medication, "id" | "created_at" | "updated_at">;

export type PrescriptionItemPayload = {
  medication_id: string;
  dose: string;
  dose_unit: string;
  frequency: string;
  route?: string;
  duration_days?: number;
  quantity: string;
  instructions?: string;
  notes?: string;
};

export type DispensingStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "WAITING_FOR_VERIFICATION"
  | "VERIFIED"
  | "WAITING_FOR_PICKUP"
  | "DISPENSED"
  | "RETURNED"
  | "CANCELLED";

export type ReturnReason =
  | "OUT_OF_STOCK"
  | "UNCLEAR_DOSAGE"
  | "UNCLEAR_INSTRUCTIONS"
  | "INCORRECT_QUANTITY"
  | "ALLERGY_RISK"
  | "DUPLICATE_MEDICATION"
  | "OTHER";

export type InventoryTransactionType =
  | "RECEIVE"
  | "RESERVE"
  | "RELEASE"
  | "DISPENSE"
  | "RETURN"
  | "ADJUST_INCREASE"
  | "ADJUST_DECREASE"
  | "EXPIRE"
  | "DISCARD";

export type InventoryBatch = {
  id: string;
  medication_id: string;
  medication: Medication;
  batch_number: string;
  expiry_date: string;
  quantity_on_hand: string;
  reserved_quantity: string;
  available_quantity: string;
  unit: string;
  location: string;
  received_at: string;
  is_active: boolean;
  created_by: string | null;
  updated_by: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

export type InventoryTransaction = {
  id: string;
  medication_id: string;
  inventory_batch_id: string;
  transaction_type: InventoryTransactionType;
  quantity: string;
  quantity_before: string;
  quantity_after: string;
  reserved_before: string;
  reserved_after: string;
  reference_type: string;
  reference_id: string | null;
  reason: string;
  performed_by: string | null;
  idempotency_key: string | null;
  created_at: string;
};

export type InventorySummary = {
  batch_count: number;
  active_batch_count: number;
  total_on_hand: string;
  total_reserved: string;
  total_available: string;
  low_stock_count: number;
  expiring_count: number;
  expired_count: number;
};

export type PharmacyQueueItem = {
  visit_id: string;
  clinic_session_id: string;
  clinic_session_name: string;
  session_date: string;
  patient_id: string;
  patient_case_number: string;
  patient_name: string;
  patient_sex: string;
  queue_number: number;
  visit_status: Visit["status"];
  prescription_id: string;
  prescription_status: PrescriptionStatus;
  dispensing_id: string | null;
  dispensing_status: DispensingStatus | null;
  item_count: number;
  total_quantity: string;
  assigned_to: string | null;
  started_at: string | null;
  prepared_at: string | null;
  verified_at: string | null;
  handed_out_at: string | null;
  notes: string;
};

export type DispensingItem = {
  id: string;
  dispensing_record_id: string;
  prescription_item_id: string;
  medication_id: string;
  prescribed_quantity: string;
  dispensed_quantity: string;
  unit: string;
  notes: string;
  inventory_batch_id: string | null;
  inventory_batch: InventoryBatch | null;
  medication: Medication;
  prescription_item: PrescriptionItem;
  created_at: string;
  updated_at: string;
};

export type DispensingRecord = {
  id: string;
  visit_id: string;
  prescription_id: string;
  status: DispensingStatus;
  assigned_to: string | null;
  started_at: string | null;
  prepared_by: string | null;
  prepared_at: string | null;
  verified_by: string | null;
  verified_at: string | null;
  verification_exception: boolean;
  verification_exception_reason: string;
  handed_out_by: string | null;
  handed_out_at: string | null;
  patient_counseling: string;
  notes: string;
  return_reason: ReturnReason | null;
  return_details: string;
  returned_by: string | null;
  returned_at: string | null;
  version: number;
  created_by: string | null;
  updated_by: string | null;
  items: DispensingItem[];
  created_at: string;
  updated_at: string;
};

export type PharmacyVisitDetail = {
  queue_item: PharmacyQueueItem;
  prescription: Prescription;
  dispensing: DispensingRecord | null;
};

export type HealthHistory = {
  id: string;
  patient_id: string;
  chronic_diseases: string;
  allergies: string;
  current_medications: string;
  surgery_history: string;
  fall_history: string;
  smoking_status: string;
  alcohol_status: string;
  sleep_status: string;
  diet_status: string;
  notes: string;
};

export type Consent = {
  id: string;
  patient_id: string;
  version: string;
  method: string;
  consented_at: string;
  staff_name: string;
  service_consent: boolean;
  research_consent: boolean;
  notes: string;
  consented_by: string | null;
  withdrawn_at: string | null;
  research_withdrawn_at: string | null;
  withdrawn_by: string | null;
};

export type Role = {
  id: string;
  name: string;
  description: string;
  permissions: string[];
};

export type ManagedUser = {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  failed_login_count: number;
  locked_until: string | null;
  last_login_at: string | null;
  roles: string[];
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  summary: string;
  created_at: string;
};

export type DashboardSummary = {
  registered: number;
  waiting_for_clinic: number;
  in_consultation: number;
  waiting_for_pharmacy: number;
  dispensing: number;
  waiting_for_verification: number;
  waiting_for_pickup: number;
  completed: number;
  cancelled: number;
  active_sessions: number;
  patient_count: number;
  medication_count: number;
  inventory_available: string;
  low_stock_count: number;
  expiring_count: number;
  expired_count: number;
};

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://backend:8000/api/v1";
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080/api/v1";
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiBaseUrl()}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("健康檢查失敗");
  }
  return response.json() as Promise<HealthResponse>;
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  if (!response.ok) {
    const error = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(error?.detail ?? "登入失敗");
  }
  return response.json() as Promise<TokenResponse>;
}

export async function logout(refreshToken: string | null): Promise<void> {
  await fetch(`${getApiBaseUrl()}/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
}

async function authenticatedFetch<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const error = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(error?.detail ?? "操作失敗");
  }
  return response.json() as Promise<T>;
}

export function listClinicSessions(accessToken: string): Promise<ClinicSession[]> {
  return authenticatedFetch<ClinicSession[]>("/clinic-sessions", accessToken);
}

export function createClinicSession(
  accessToken: string,
  payload: Omit<ClinicSession, "id" | "notes"> & { notes?: string }
): Promise<ClinicSession> {
  return authenticatedFetch<ClinicSession>("/clinic-sessions", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listPatients(accessToken: string, query = ""): Promise<Patient[]> {
  const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
  return authenticatedFetch<Patient[]>(`/patients${suffix}`, accessToken);
}

export function getPatient(accessToken: string, patientId: string): Promise<Patient> {
  return authenticatedFetch<Patient>(`/patients/${patientId}`, accessToken);
}

export function updatePatient(
  accessToken: string,
  patientId: string,
  payload: Partial<Omit<Patient, "id">>
): Promise<Patient> {
  return authenticatedFetch<Patient>(`/patients/${patientId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createPatient(
  accessToken: string,
  payload: Omit<Patient, "id" | "is_active">
): Promise<Patient> {
  return authenticatedFetch<Patient>("/patients", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createVisit(
  accessToken: string,
  payload: { clinic_session_id: string; patient_id: string; registration_staff: string; notes?: string }
): Promise<Visit> {
  return authenticatedFetch<Visit>("/visits", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getHealthHistory(accessToken: string, patientId: string): Promise<HealthHistory> {
  return authenticatedFetch<HealthHistory>(`/patients/${patientId}/health-history`, accessToken);
}

export function upsertHealthHistory(
  accessToken: string,
  patientId: string,
  payload: Omit<HealthHistory, "id" | "patient_id">
): Promise<HealthHistory> {
  return authenticatedFetch<HealthHistory>(`/patients/${patientId}/health-history`, accessToken, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listPatientConsents(accessToken: string, patientId: string): Promise<Consent[]> {
  return authenticatedFetch<Consent[]>(`/patients/${patientId}/consents`, accessToken);
}

export function createPatientConsent(
  accessToken: string,
  patientId: string,
  payload: {
    version: string;
    method: string;
    consented_at: string;
    staff_name: string;
    service_consent: boolean;
    research_consent?: boolean;
    notes?: string;
  }
): Promise<Consent> {
  return authenticatedFetch<Consent>(`/patients/${patientId}/consents`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function withdrawResearchConsent(
  accessToken: string,
  patientId: string,
  consentId: string,
  notes = ""
): Promise<Consent> {
  return authenticatedFetch<Consent>(`/patients/${patientId}/consents/${consentId}/withdraw-research`, accessToken, {
    method: "POST",
    body: JSON.stringify({ notes })
  });
}

export function updateVisitStatus(accessToken: string, visitId: string, status: Visit["status"]): Promise<Visit> {
  return authenticatedFetch<Visit>(`/visits/${visitId}/status`, accessToken, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}

export function listClinicQueue(accessToken: string): Promise<ClinicQueueItem[]> {
  return authenticatedFetch<ClinicQueueItem[]>("/clinic/queue", accessToken);
}

export function getClinicQueueItem(accessToken: string, visitId: string): Promise<ClinicQueueItem> {
  return authenticatedFetch<ClinicQueueItem>(`/clinic/queue/${visitId}`, accessToken);
}

export function startClinicVisit(accessToken: string, visitId: string): Promise<ClinicQueueItem> {
  return authenticatedFetch<ClinicQueueItem>(`/clinic/queue/${visitId}/start`, accessToken, { method: "POST" });
}

export function cancelClinicVisit(accessToken: string, visitId: string): Promise<ClinicQueueItem> {
  return authenticatedFetch<ClinicQueueItem>(`/clinic/queue/${visitId}/cancel`, accessToken, { method: "POST" });
}

export function listVitalSigns(accessToken: string, visitId: string): Promise<VitalSign[]> {
  return authenticatedFetch<VitalSign[]>(`/visits/${visitId}/vital-signs`, accessToken);
}

export function createVitalSign(
  accessToken: string,
  visitId: string,
  payload: Partial<Omit<VitalSign, "id" | "visit_id" | "measured_by" | "created_at" | "updated_at">>
): Promise<VitalSign> {
  return authenticatedFetch<VitalSign>(`/visits/${visitId}/vital-signs`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getConsultation(accessToken: string, visitId: string): Promise<Consultation> {
  return authenticatedFetch<Consultation>(`/visits/${visitId}/consultation`, accessToken);
}

export function updateConsultationIntake(
  accessToken: string,
  visitId: string,
  payload: Partial<Consultation>
): Promise<Consultation> {
  return authenticatedFetch<Consultation>(`/visits/${visitId}/consultation/intake`, accessToken, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function updateConsultationClinical(
  accessToken: string,
  visitId: string,
  payload: Partial<Consultation>
): Promise<Consultation> {
  return authenticatedFetch<Consultation>(`/visits/${visitId}/consultation/clinical`, accessToken, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function completeConsultation(
  accessToken: string,
  visitId: string,
  payload: { requires_pharmacy?: boolean; clinician_notes?: string }
): Promise<Consultation> {
  return authenticatedFetch<Consultation>(`/visits/${visitId}/consultation/complete`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listMedications(accessToken: string, query = "", activeOnly = false): Promise<Medication[]> {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (activeOnly) params.set("active_only", "true");
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return authenticatedFetch<Medication[]>(`/medications${suffix}`, accessToken);
}

export function createMedication(accessToken: string, payload: MedicationPayload): Promise<Medication> {
  return authenticatedFetch<Medication>("/medications", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateMedication(
  accessToken: string,
  medicationId: string,
  payload: Partial<MedicationPayload>
): Promise<Medication> {
  return authenticatedFetch<Medication>(`/medications/${medicationId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function activateMedication(accessToken: string, medicationId: string): Promise<Medication> {
  return authenticatedFetch<Medication>(`/medications/${medicationId}/activate`, accessToken, { method: "POST" });
}

export function deactivateMedication(accessToken: string, medicationId: string): Promise<Medication> {
  return authenticatedFetch<Medication>(`/medications/${medicationId}/deactivate`, accessToken, { method: "POST" });
}

export function getPrescription(accessToken: string, visitId: string): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/visits/${visitId}/prescription`, accessToken);
}

export function createPrescription(accessToken: string, visitId: string): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/visits/${visitId}/prescription`, accessToken, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function addPrescriptionItem(
  accessToken: string,
  prescriptionId: string,
  payload: PrescriptionItemPayload
): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescriptions/${prescriptionId}/items`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updatePrescriptionItem(
  accessToken: string,
  itemId: string,
  payload: Partial<PrescriptionItemPayload>
): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescription-items/${itemId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function deletePrescriptionItem(accessToken: string, itemId: string): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescription-items/${itemId}`, accessToken, { method: "DELETE" });
}

export function confirmPrescription(accessToken: string, prescriptionId: string): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescriptions/${prescriptionId}/confirm`, accessToken, { method: "POST" });
}

export function sendPrescriptionToPharmacy(accessToken: string, prescriptionId: string): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescriptions/${prescriptionId}/send-to-pharmacy`, accessToken, {
    method: "POST"
  });
}

export function voidPrescription(accessToken: string, prescriptionId: string, reason = ""): Promise<Prescription> {
  return authenticatedFetch<Prescription>(`/prescriptions/${prescriptionId}/void`, accessToken, {
    method: "POST",
    body: JSON.stringify({ reason })
  });
}

export function listPharmacyQueue(accessToken: string, query = "", status = ""): Promise<PharmacyQueueItem[]> {
  const params = new URLSearchParams();
  if (query) params.set("search", query);
  if (status) params.set("status", status);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return authenticatedFetch<PharmacyQueueItem[]>(`/pharmacy/queue${suffix}`, accessToken);
}

export function getPharmacyVisit(accessToken: string, visitId: string): Promise<PharmacyVisitDetail> {
  return authenticatedFetch<PharmacyVisitDetail>(`/pharmacy/queue/${visitId}`, accessToken);
}

export function startDispensing(accessToken: string, visitId: string): Promise<PharmacyVisitDetail> {
  return authenticatedFetch<PharmacyVisitDetail>(`/pharmacy/queue/${visitId}/start`, accessToken, { method: "POST" });
}

export function updateDispensingItems(
  accessToken: string,
  dispensingId: string,
  payload: { items: Array<{ id: string; dispensed_quantity: string; notes?: string }>; notes?: string }
): Promise<DispensingRecord> {
  return authenticatedFetch<DispensingRecord>(`/dispensing/${dispensingId}/items`, accessToken, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function submitDispensingForVerification(
  accessToken: string,
  dispensingId: string
): Promise<DispensingRecord> {
  return authenticatedFetch<DispensingRecord>(`/dispensing/${dispensingId}/submit-for-verification`, accessToken, {
    method: "POST"
  });
}

export function verifyDispensing(
  accessToken: string,
  dispensingId: string,
  payload: { allow_self_verification?: boolean; exception_reason?: string }
): Promise<DispensingRecord> {
  return authenticatedFetch<DispensingRecord>(`/dispensing/${dispensingId}/verify`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function handOutMedication(
  accessToken: string,
  dispensingId: string,
  payload: { patient_counseling: string; notes?: string; idempotency_key: string }
): Promise<DispensingRecord> {
  return authenticatedFetch<DispensingRecord>(`/dispensing/${dispensingId}/hand-out`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function returnDispensingToClinic(
  accessToken: string,
  dispensingId: string,
  payload: { reason: ReturnReason; details: string }
): Promise<DispensingRecord> {
  return authenticatedFetch<DispensingRecord>(`/dispensing/${dispensingId}/return-to-clinic`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listInventoryBatches(accessToken: string, query = ""): Promise<InventoryBatch[]> {
  const params = new URLSearchParams();
  if (query) params.set("search", query);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return authenticatedFetch<InventoryBatch[]>(`/inventory${suffix}`, accessToken);
}

export function getInventorySummary(accessToken: string): Promise<InventorySummary> {
  return authenticatedFetch<InventorySummary>("/inventory/summary", accessToken);
}

export function createInventoryBatch(
  accessToken: string,
  payload: {
    medication_id: string;
    batch_number: string;
    expiry_date: string;
    quantity: string;
    unit: string;
    location?: string;
    received_at?: string;
  }
): Promise<InventoryBatch> {
  return authenticatedFetch<InventoryBatch>("/inventory/batches", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateInventoryBatch(
  accessToken: string,
  batchId: string,
  payload: Partial<Pick<InventoryBatch, "batch_number" | "expiry_date" | "unit" | "location" | "is_active">>
): Promise<InventoryBatch> {
  return authenticatedFetch<InventoryBatch>(`/inventory/batches/${batchId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createInventoryAdjustment(
  accessToken: string,
  payload: { batch_id: string; adjustment_type: InventoryTransactionType; quantity: string; reason: string }
): Promise<InventoryBatch> {
  return authenticatedFetch<InventoryBatch>("/inventory/adjustments", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listInventoryTransactions(accessToken: string, medicationId = ""): Promise<InventoryTransaction[]> {
  const suffix = medicationId ? `?medication_id=${encodeURIComponent(medicationId)}` : "";
  return authenticatedFetch<InventoryTransaction[]>(`/inventory/transactions${suffix}`, accessToken);
}

export function listAvailableBatches(accessToken: string, medicationId: string): Promise<InventoryBatch[]> {
  return authenticatedFetch<InventoryBatch[]>(`/medications/${medicationId}/available-batches`, accessToken);
}

export function getDashboardSummary(accessToken: string): Promise<DashboardSummary> {
  return authenticatedFetch<DashboardSummary>("/dashboard/summary", accessToken);
}

export function listRoles(accessToken: string): Promise<Role[]> {
  return authenticatedFetch<Role[]>("/roles", accessToken);
}

export function listUsers(accessToken: string): Promise<ManagedUser[]> {
  return authenticatedFetch<ManagedUser[]>("/users", accessToken);
}

export function createUser(
  accessToken: string,
  payload: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    roles: string[];
    is_active?: boolean;
  }
): Promise<ManagedUser> {
  return authenticatedFetch<ManagedUser>("/users", accessToken, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateUser(
  accessToken: string,
  userId: string,
  payload: { email?: string; full_name?: string; roles?: string[]; is_active?: boolean; unlock?: boolean }
): Promise<ManagedUser> {
  return authenticatedFetch<ManagedUser>(`/users/${userId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function resetUserPassword(accessToken: string, userId: string, password: string): Promise<ManagedUser> {
  return authenticatedFetch<ManagedUser>(`/users/${userId}/reset-password`, accessToken, {
    method: "POST",
    body: JSON.stringify({ password })
  });
}

export function listAuditLogs(
  accessToken: string,
  filters: { action?: string; entity_type?: string; q?: string; limit?: number } = {}
): Promise<AuditLog[]> {
  const params = new URLSearchParams();
  if (filters.action) params.set("action", filters.action);
  if (filters.entity_type) params.set("entity_type", filters.entity_type);
  if (filters.q) params.set("q", filters.q);
  if (filters.limit) params.set("limit", String(filters.limit));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return authenticatedFetch<AuditLog[]>(`/audit-logs${suffix}`, accessToken);
}
