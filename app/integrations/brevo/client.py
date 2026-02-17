"""Brevo API client with circuit breaker and retry logic."""
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.circuit_breaker import circuit_breaker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BrevoClient:
    """Brevo API client."""
    
    BASE_URL = "https://api.brevo.com/v3"
    
    def __init__(self):
        """Initialize Brevo client."""
        self.api_key = settings.brevo_api_key
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
    
    @circuit_breaker(name="brevo_api", failure_threshold=5, recovery_timeout=60)
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Brevo API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            Response data
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Brevo API error: {str(e)}")
                raise
    
    async def send_sms(self, to: str, content: str, sender: Optional[str] = None) -> Dict[str, Any]:
        """
        Send SMS via Brevo.
        
        Args:
            to: Phone number
            content: Message content
            sender: Sender name
            
        Returns:
            API response
        """
        data = {
            "sender": sender or settings.brevo_sms_sender,
            "recipient": to,
            "content": content,
            "type": "transactional"
        }
        
        return await self._make_request("POST", "transactionalSMS/sms", data)
    
    async def send_whatsapp(self, to: str, content: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send WhatsApp message via Brevo.
        
        Args:
            to: Phone number
            content: Message content
            template_id: Optional template ID
            
        Returns:
            API response
        """
        data = {
            "to": to,
            "type": "text",
            "text": {"body": content}
        }
        
        if template_id:
            data["type"] = "template"
            data["template"] = {"id": template_id}
        
        return await self._make_request("POST", "whatsapp/sendMessage", data)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        sender: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Brevo.
        
        Args:
            to: Recipient email
            subject: Email subject
            html_content: HTML content
            sender: Sender info
            
        Returns:
            API response
        """
        data = {
            "sender": sender or {
                "email": settings.brevo_email_sender,
                "name": settings.app_name
            },
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html_content
        }
        
        return await self._make_request("POST", "smtp/email", data)


# Global Brevo client instance
brevo_client = BrevoClient()
