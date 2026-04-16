import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import EmailRequest, EmailResponse
from app.core.chains import STRATEGY_MAP

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=EmailResponse)
async def generate_email(request: EmailRequest) -> EmailResponse:
    """Generate a professional email from intent, key facts, and tone."""
    if request.strategy not in STRATEGY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{request.strategy}'. Choose from: {list(STRATEGY_MAP.keys())}",
        )

    generator = STRATEGY_MAP[request.strategy]
    logger.info("Generating email | strategy=%s tone=%s", request.strategy, request.tone)

    try:
        result = await generator(
            intent=request.intent,
            key_facts=request.key_facts,
            tone=request.tone,
        )
    except Exception as e:
        logger.exception("Email generation failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return EmailResponse(
        email=result.email,
        model_name=result.model_name,
        strategy=result.strategy,
        was_revised=result.was_revised,
    )
