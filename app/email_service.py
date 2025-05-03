import json
import os
from dataclasses import asdict
from datetime import datetime

import pystache
import requests
from dotenv import load_dotenv

from message_model import MySessionInfo


def generate_email_body(input:MySessionInfo):
    dict = asdict(input)
    dict["appointment_range"] = format_appointment_range(dict["appointment_start_time"], dict["appointment_end_time"])
    dict["clinic_name"] = "assort health related clinic"
    dict["office_contact_info"] = "1234567890"
    non_empty_dict= {k:v for k,v in dict.items() if v is not None}

    notification_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Appointment Confirmation</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
  <h2>Appointment Confirmation for {{patient_name}} </h2>

  <p>Dear <strong>{{appointment_provider}}</strong>,</p>

  <p>We are confirming the appointment details for your referred patient. Please see the information below:</p>

  <hr>

  <h3>🧑‍⚕️ Patient Information</h3>
  <ul>
    <li><strong>Name:</strong> {{patient_name}}</li>
    <li><strong>Date of Birth:</strong> {{patient_dob}}</li>
    <li><strong>Address:</strong> {{patient_address}}</li>
    <li><strong>Phone:</strong> {{patient_phone}}</li>
    <li><strong>Email:</strong> {{patient_email}}</li>
    <li><strong>Chief Medical Complaint:</strong> {{chief_medical_complaint}}</li>
  </ul>

  <h3>💳 Insurance Information</h3>
  <ul>
    <li><strong>Payer Name:</strong> {{insurance_payer_name}}</li>
    <li><strong>Insurance ID:</strong> {{insurance_id}}</li>
  </ul>

  <h3>📄 Referral Details</h3>
  <ul>
    <li><strong>Referring Physician:</strong> {{referral_physician}}</li>
  </ul>

  <h3>📅 Appointment Details</h3>
  <ul>
    <li><strong>Provider:</strong> {{appointment_provider}}</li>
    <li><strong>Date & Time:</strong> {{appointment_range}}</li>
  </ul>

  <hr>

  <p>If you have any questions or need to reschedule, please contact us at {{office_contact_info}}.</p>

  <p>Thank you<br>
  <!-- <strong>{{your_name}}</strong><br> -->
{{clinic_name}}<br>
  <!-- {{your_phone}} | {{your_email}}</p> -->
  </p>
</body>
</html>
"""
    return pystache.render(notification_template, non_empty_dict)


def format_appointment_range(start_str: str,end_str:str) -> str|None:
    try:
        if not start_str or not end_str:
            return None
        start_dt = datetime.strptime(start_str, "%m/%d/%Y %H:%M")
        end_dt = datetime.strptime(end_str, "%m/%d/%Y %H:%M")

        # Format output
        if start_dt.date() == end_dt.date():
            return f"{start_dt.strftime('%B %-d, %Y')}, {start_dt.strftime('%-I:%M %p')} – {end_dt.strftime('%-I:%M %p')}"
        else:
            return f"{start_dt.strftime('%B %-d, %Y, %-I:%M %p')} – {end_dt.strftime('%B %-d, %Y, %-I:%M %p')}"

    except ValueError as e:
        return f"Invalid input format: {e}"


def send_email(to_email: str,input:MySessionInfo):
    url = f"https://open.larksuite.com/open-apis/mail/v1/user_mailboxes/me/messages/send"
    payload = json.dumps(
        {
            "subject": "Confirmation",
            "to": [
                {
                    "mail_address": to_email,
                    "name": "Mike"
                }
            ],

            "head_from": {
                "name": "Notification"
            },
            "body_html": generate_email_body(input),
        }
    )
    print("payload",payload)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('LARK_TOKEN')}" ,
        "Content-Type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

if __name__ == "__main__":
    load_dotenv()
    # Send a testing email to me
    send_email("bl2684@nyu.edu", MySessionInfo(patient_address="444 5216 Rr"))
