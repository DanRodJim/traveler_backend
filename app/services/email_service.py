import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


class EmailService:
    def send_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        trip_title: str,
        role: str,
        invite_url: str,
    ) -> bool:
        subject = f"{inviter_name} invited you to join \"{trip_title}\" on Travel Planner"

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
            <h2 style="color: #2563eb;">You've been invited to a trip!</h2>
            <p><strong>{inviter_name}</strong> invited you to join <strong>{trip_title}</strong>
            as a{"n" if role == "editor" else ""} <strong>{role}</strong>.</p>
            <div style="margin: 24px 0;">
                <a href="{invite_url}"
                   style="background: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    View Invitation
                </a>
            </div>
            <p style="color: #6b7280; font-size: 13px;">
                This invitation expires in 7 days. If you didn't expect this email,
                you can safely ignore it.
            </p>
        </div>
        """

        return self._send(to_email, subject, html)

    def send_trip_reminder_email(
        self,
        to_email: str,
        user_name: str,
        trip_title: str,
        days_until: int,
        trip_url: str,
    ) -> bool:
        time_phrase = "tomorrow" if days_until == 1 else f"in {days_until} days"
        subject = f"Your trip \"{trip_title}\" starts {time_phrase}!"

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Trip reminder</h2>
            <p>Hi {user_name},</p>
            <p><strong>{trip_title}</strong> starts <strong>{time_phrase}</strong>. Time to finish packing!</p>
            <div style="margin: 24px 0;">
                <a href="{trip_url}"
                   style="background: #2563eb; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    View Trip
                </a>
            </div>
        </div>
        """

        return self._send(to_email, subject, html)

    def _send(self, to_email: str, subject: str, html: str) -> bool:
        try:
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            })
            return True
        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {e}")
            return False