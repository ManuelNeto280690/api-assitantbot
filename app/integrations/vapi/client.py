"""VAPI API client for voice calls."""
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.circuit_breaker import circuit_breaker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VAPIClient:
    """VAPI API client for voice calls."""
    
    BASE_URL = "https://api.vapi.ai"
    
    def __init__(self):
        """Initialize VAPI client."""
        self.api_key = settings.vapi_api_key
        self.phone_number = settings.vapi_phone_number
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    @circuit_breaker(name="vapi_api", failure_threshold=5, recovery_timeout=60)
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to VAPI API.
        
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
                logger.error(f"VAPI API error: {str(e)}")
                raise
    
    async def create_call(
        self,
        phone_number: str,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create outbound voice call.
        
        Args:
            phone_number: Recipient phone number
            assistant_id: VAPI assistant ID
            metadata: Optional metadata
            
        Returns:
            Call details
        """
        data = {
            "phoneNumber": phone_number,
            "assistantId": assistant_id,
            "phoneNumberId": self.phone_number,
        }
        
        if metadata:
            data["metadata"] = metadata
        
        return await self._make_request("POST", "call", data)
    
    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Get call details.
        
        Args:
            call_id: Call ID
            
        Returns:
            Call details
        """
        return await self._make_request("GET", f"call/{call_id}")


# Global VAPI client instance
vapi_client = VAPIClient()
