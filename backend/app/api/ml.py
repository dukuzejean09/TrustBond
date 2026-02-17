"""ML prediction endpoints — trigger and retrieve model predictions."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/predict")
async def predict_authenticity():
    """Run Random Forest on report's feature_vector → write to ml_predictions."""
    # TODO: load model, predict, store result with model_version, model_type, confidence, explanation
    pass


@router.get("/report/{report_id}")
async def get_predictions(report_id: str):
    """Get all ML predictions for a report (may include anomaly, vision, random_forest)."""
    pass
