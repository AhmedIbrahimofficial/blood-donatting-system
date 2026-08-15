"""
Email notification service using SendGrid.

Sends:
1. Donor alert email — when a new blood request matches a donor
2. Request confirmation — to the requester after submitting
3. Match accepted — to requester when a donor accepts
"""
from __future__ import annotations

import logging
from typing import List

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to_email: str, subject: str, html_content: str) -> bool:
    """Send a single email. Returns True on success, False on failure."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — email skipped: %s", subject)
        return False

    try:
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info("Email sent to %s — status %d", to_email, response.status_code)
        return response.status_code in (200, 202)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

def send_donor_alert(
    donor_email: str,
    donor_name: str,
    blood_type: str,
    hospital_name: str,
    urgency_level: str,
    request_id: int,
) -> bool:
    """Alert a matched donor about an emergency blood request."""
    urgency_color = {
        "critical": "#dc2626",
        "urgent": "#d97706",
        "planned": "#2563eb",
    }.get(urgency_level, "#6b7280")

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background-color: #dc2626; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🩸 LifeLink — Blood Needed</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; color: #374151;">Dear <strong>{donor_name}</strong>,</p>
        <p style="font-size: 16px; color: #374151;">
          A patient near you urgently needs <strong>{blood_type}</strong> blood.
          You are a compatible donor. Please consider helping.
        </p>

        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 24px 0;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Blood Type Needed</td>
              <td style="padding: 8px 0; font-weight: bold; font-size: 14px;">{blood_type}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Hospital</td>
              <td style="padding: 8px 0; font-weight: bold; font-size: 14px;">{hospital_name}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Urgency</td>
              <td style="padding: 8px 0;">
                <span style="background:{urgency_color}; color:white; padding: 2px 10px; border-radius: 4px; font-size: 13px; font-weight: bold;">
                  {urgency_level.upper()}
                </span>
              </td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">Request ID</td>
              <td style="padding: 8px 0; font-weight: bold; font-size: 14px;">#{request_id}</td>
            </tr>
          </table>
        </div>

        <p style="font-size: 14px; color: #6b7280;">
          Log in to your LifeLink dashboard to accept or decline this request.
        </p>
        <p style="font-size: 12px; color: #9ca3af; margin-top: 32px;">
          You are receiving this because you registered as an available donor on LifeLink.
          To stop receiving alerts, update your availability in your dashboard.
        </p>
      </div>
    </div>
    """
    return _send(
        to_email=donor_email,
        subject=f"🩸 Urgent: {blood_type} blood needed at {hospital_name}",
        html_content=html,
    )


def send_request_confirmation(
    requester_email: str,
    requester_name: str,
    blood_type: str,
    hospital_name: str,
    request_id: int,
    candidates_found: int,
) -> bool:
    """Confirm to the requester that their request was received and donors alerted."""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background-color: #16a34a; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">✅ Request Received — LifeLink</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; color: #374151;">Dear <strong>{requester_name}</strong>,</p>
        <p style="font-size: 16px; color: #374151;">
          Your emergency blood request has been received.
          <strong>{candidates_found} compatible donor(s)</strong> near {hospital_name} have been alerted.
        </p>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 24px 0;">
          <p style="margin: 0; font-size: 14px; color: #166534;">
            <strong>Request ID:</strong> #{request_id}<br>
            <strong>Blood Type:</strong> {blood_type}<br>
            <strong>Hospital:</strong> {hospital_name}
          </p>
        </div>
        <p style="font-size: 14px; color: #6b7280;">
          Donors will contact the hospital directly once they accept.
          For emergencies also call: <strong>1122</strong>
        </p>
      </div>
    </div>
    """
    return _send(
        to_email=requester_email,
        subject=f"✅ Blood Request #{request_id} — {candidates_found} donor(s) alerted",
        html_content=html,
    )


def send_match_accepted(
    requester_email: str,
    requester_name: str,
    donor_name: str,
    blood_type: str,
    hospital_name: str,
) -> bool:
    """Notify requester that a donor has accepted their request."""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background-color: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🎉 Donor Found — LifeLink</h1>
      </div>
      <div style="background: #fff; padding: 32px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; color: #374151;">Dear <strong>{requester_name}</strong>,</p>
        <p style="font-size: 16px; color: #374151;">
          Great news! <strong>{donor_name}</strong> has accepted your blood request
          and will be heading to <strong>{hospital_name}</strong>.
        </p>
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 24px 0;">
          <p style="margin: 0; font-size: 14px; color: #1e40af;">
            <strong>Blood Type:</strong> {blood_type}<br>
            <strong>Hospital:</strong> {hospital_name}<br>
            <strong>Donor:</strong> {donor_name}
          </p>
        </div>
        <p style="font-size: 14px; color: #6b7280;">
          Please ensure the hospital blood bank is ready to receive the donation.
        </p>
      </div>
    </div>
    """
    return _send(
        to_email=requester_email,
        subject=f"🎉 Donor found for your {blood_type} request at {hospital_name}",
        html_content=html,
    )
