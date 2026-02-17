"""Webhook endpoints for external integrations."""
from fastapi import APIRouter, Request, HTTPException, status, Header
from typing import Optional
import hashlib
import hmac

from app.config import settings
from app.integrations.vapi.voice import handle_voice_webhook
from app.utils.idempotency import idempotency_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/brevo/sms")
async def brevo_sms_webhook(
    request: Request,
    x_sib_signature: Optional[str] = Header(None)
):
    """Handle Brevo SMS webhook."""
    body = await request.json()
    
    # Generate idempotency key
    idempotency_key = idempotency_service.generate_key(
        "brevo_sms",
        body.get("message-id", ""),
        body.get("event", "")
    )
    
    # Check if already processed
    if idempotency_service.is_processed(idempotency_key):
        logger.info("Webhook already processed", idempotency_key=idempotency_key)
        return {"status": "already_processed"}
    
    # Process webhook
    logger.info("Processing Brevo SMS webhook", body=body)
    
    # Mark as processed
    idempotency_service.mark_processed(idempotency_key)
    
    return {"status": "ok"}


@router.post("/brevo/email")
async def brevo_email_webhook(
    request: Request,
    x_sib_signature: Optional[str] = Header(None)
):
    """Handle Brevo email webhook."""
    body = await request.json()
    
    # Generate idempotency key
    idempotency_key = idempotency_service.generate_key(
        "brevo_email",
        body.get("message-id", ""),
        body.get("event", "")
    )
    
    # Check if already processed
    if idempotency_service.is_processed(idempotency_key):
        logger.info("Webhook already processed", idempotency_key=idempotency_key)
        return {"status": "already_processed"}
    
    # Process webhook
    logger.info("Processing Brevo email webhook", body=body)
    
    # Publish events for email tracking
    event_type = body.get("event")
    if event_type == "opened":
        # Publish email_opened event
        pass
    elif event_type == "click":
        # Publish email_clicked event
        pass
    
    # Mark as processed
    idempotency_service.mark_processed(idempotency_key)
    
    return {"status": "ok"}


@router.post("/vapi/call-status")
async def vapi_call_status_webhook(request: Request):
    """Handle VAPI call status webhook."""
    body = await request.json()
    
    call_id = body.get("call", {}).get("id")
    status_value = body.get("status")
    
    if not call_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing call ID"
        )
    
    # Generate idempotency key
    idempotency_key = idempotency_service.generate_key(
        "vapi_call",
        call_id,
        status_value
    )
    
    # Check if already processed
    if idempotency_service.is_processed(idempotency_key):
        logger.info("Webhook already processed", idempotency_key=idempotency_key)
        return {"status": "already_processed"}
    
    # Process webhook
    logger.info("Processing VAPI webhook", call_id=call_id, status=status_value)
    
    # Handle voice webhook
    metadata = body.get("call", {}).get("metadata", {})
    await handle_voice_webhook(call_id, status_value, metadata)
    
    # Mark as processed
    idempotency_service.mark_processed(idempotency_key)
    
    return {"status": "ok"}
