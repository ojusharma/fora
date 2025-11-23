"""Email service for sending notifications."""

import logging
from typing import Optional
from uuid import UUID
import resend
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self, supabase_client=None):
        """Initialize email service."""
        self.supabase = supabase_client
    
    async def send_reward_claim_email(
        self,
        user_email: str,
        reward_title: str,
        credits_spent: int,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send congratulations email when user claims a reward.
        
        Args:
            user_email: User's email address
            reward_title: Name of the reward claimed
            credits_spent: Number of credits spent
            user_name: Optional user display name
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # For now, we'll use Supabase's built-in email functionality
            # In production, you might want to use a service like SendGrid, AWS SES, etc.
            
            subject = f"🎉 Congratulations on Redeeming {reward_title}!"
            
            greeting = f"Hi {user_name}!" if user_name else "Hi!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f9f9f9;
                        padding: 30px;
                        border-radius: 0 0 10px 10px;
                    }}
                    .reward-box {{
                        background: white;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .credits {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #667eea;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Reward Redeemed!</h1>
                    </div>
                    <div class="content">
                        <p>{greeting}</p>
                        
                        <p>Congratulations on redeeming your reward!</p>
                        
                        <div class="reward-box">
                            <h2 style="margin-top: 0; color: #667eea;">{reward_title}</h2>
                            <p style="margin: 10px 0;">
                                <span style="color: #666;">Credits spent:</span> 
                                <span class="credits">{credits_spent}</span>
                            </p>
                        </div>
                        
                        <p>Your reward has been successfully claimed. Thank you for being an active member of our community!</p>
                        
                        <p>Keep earning credits by completing tasks and engaging with the platform to unlock more exciting rewards.</p>
                        
                        <p>Best regards,<br>The Fora Team</p>
                        
                        <div class="footer">
                            <p>This is an automated email. Please do not reply.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            {greeting}
            
            Congratulations on redeeming your reward!
            
            Reward: {reward_title}
            Credits spent: {credits_spent}
            
            Your reward has been successfully claimed. Thank you for being an active member of our community!
            
            Keep earning credits by completing tasks and engaging with the platform to unlock more exciting rewards.
            
            Best regards,
            The Fora Team
            """
            
            # Get configuration from Settings
            settings = get_settings()
            resend_api_key = settings.resend_api_key
            from_email = settings.from_email
            
            if not resend_api_key:
                # Fallback to logging if no API key configured
                logger.warning("RESEND_API_KEY not set - emails will only be logged")
                logger.info(f"Would send email to {user_email}: {subject}")
                logger.debug(f"Email content: {text_content}")
                return True
            
            # Send email via Resend
            try:
                resend.api_key = resend_api_key
                
                params = {
                    "from": from_email,
                    "to": [user_email],
                    "subject": subject,
                    "html": html_content,
                    "text": text_content,
                }
                
                email = resend.Emails.send(params)
                logger.info(f"✓ Email sent successfully to {user_email} - ID: {email.get('id', 'unknown')}")
                return True
                
            except Exception as email_error:
                logger.error(f"✗ Resend API error: {email_error}")
                # Still log the email content for debugging
                logger.info(f"Email that failed to send to {user_email}: {subject}")
                logger.debug(f"Email content: {text_content}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reward claim email: {e}")
            return False
    
    async def send_reward_claim_notification(
        self,
        user_id: UUID,
        reward_title: str,
        credits_spent: int
    ) -> bool:
        """
        Send reward claim notification (get user details and send email).
        
        Args:
            user_id: User's UUID
            reward_title: Name of the reward claimed
            credits_spent: Number of credits spent
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            if not self.supabase:
                logger.warning("Supabase client not initialized, cannot send email")
                return False
            
            # Get user details from auth.users
            user_response = self.supabase.auth.admin.get_user_by_id(str(user_id))
            
            if not user_response or not user_response.user:
                logger.error(f"User {user_id} not found")
                return False
            
            user = user_response.user
            user_email = user.email
            user_name = user.user_metadata.get("display_name") if user.user_metadata else None
            
            # Send email
            return await self.send_reward_claim_email(
                user_email=user_email,
                reward_title=reward_title,
                credits_spent=credits_spent,
                user_name=user_name
            )
            
        except Exception as e:
            logger.error(f"Failed to send reward claim notification: {e}")
            return False


# Singleton instance
_email_service = None


def get_email_service(supabase_client=None) -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService(supabase_client)
    return _email_service
