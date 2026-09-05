from fastapi import APIRouter
from app.schemas.ai_estimator import AiEstimatorRequest, AiEstimatorResponse
from app.services.ai_estimator_service import AiEstimatorService
from app.auth.dependencies import CurrentUser

router = APIRouter(prefix="/api/ai-estimator", tags=["ai-estimator"])


@router.post("/estimate")
def generate_estimate(
    request: AiEstimatorRequest,
    current_user: CurrentUser
) -> AiEstimatorResponse:
    service = AiEstimatorService()
    return service.generate_estimate(request)