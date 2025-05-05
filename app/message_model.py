from dataclasses import dataclass


@dataclass
class MySessionInfo:
    """
    Represents session information for a patient.
    """
    patient_name: str | None = None
    patient_dob: str | None = None
    insurance_payer_name: str | None = None
    insurance_id: int | None = None

    has_referral: bool | None = None
    referral_physician: str | None = None

    medical_complaint: str | None = None
    patient_address: str | None = None

    patient_email: str | None = None
    patient_phone: str | None = None

    appointment_provider: str | None = None
    appointment_start_time: str | None = None
    appointment_end_time: str | None = None