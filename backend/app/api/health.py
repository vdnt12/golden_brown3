from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """Section 25: GET /api/health -> {'status': 'ok'}."""
    return {"status": "ok"}
