from fastapi import APIRouter, Depends
from app.schemas.ai_estimator import AiEstimatorRequest, AiEstimatorResponse
from app.services.ai_estimator_service import AiEstimatorService
from app.auth.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/ai-estimator", tags=["ai-estimator"])


@router.post("/estimate", response_model=AiEstimatorResponse)
async def generate_estimate(
    request: AiEstimatorRequest,
    current_user: User = Depends(get_current_active_user),
) -> AiEstimatorResponse:
    service = AiEstimatorService()
    return await service.generate_estimate(request)