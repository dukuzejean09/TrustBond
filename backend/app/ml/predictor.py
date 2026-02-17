"""Random Forest predictor — load model and run inference."""

from pathlib import Path
from typing import Dict, Any
import joblib
import pandas as pd


class Predictor:
    """Loads trained Random Forest model (pipeline) and predicts report authenticity.

    Expects the training step to have saved a dict with keys:
      - "pipeline": sklearn Pipeline (preprocessor + classifier)
      - "label_encoder": sklearn.preprocessing.LabelEncoder

    The saved file path is `trained_models/random_forest.joblib`.
    """

    MODEL_PATH = Path(__file__).parent / "trained_models" / "random_forest.joblib"

    # map dataset labels -> API prediction labels
    LABEL_TO_PRED = {"Verified": "likely_real", "Pending": "suspicious", "Rejected": "fake"}

    def __init__(self):
        self.pipeline = None
        self.label_encoder = None

    def load_model(self):
        """Load trained pipeline + label encoder saved by the training script."""
        if not self.MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {self.MODEL_PATH}")
        data = joblib.load(self.MODEL_PATH)
        # saved object is a dict {"pipeline": Pipeline, "label_encoder": LabelEncoder}
        self.pipeline = data.get("pipeline")
        self.label_encoder = data.get("label_encoder")
        if self.pipeline is None or self.label_encoder is None:
            raise RuntimeError("Loaded model missing pipeline or label_encoder")

    def predict(self, feature_vector: dict) -> Dict[str, Any]:
        """Run inference for a single report feature vector.

        feature_vector: mapping of feature_name -> value (must match training columns)
        """
        if self.pipeline is None:
            self.load_model()

        # Ensure single-row DataFrame with same column order as training expects
        X = pd.DataFrame([feature_vector])

        # Predict class (encoded) and probabilities
        encoded_pred = self.pipeline.predict(X)[0]
        probs = None
        try:
            probs = self.pipeline.predict_proba(X)[0]
        except Exception:
            probs = None

        # Decode label
        pred_label_raw = self.label_encoder.inverse_transform([encoded_pred])[0]
        prediction_label = self.LABEL_TO_PRED.get(pred_label_raw, pred_label_raw)

        confidence = float(probs.max()) if probs is not None else 1.0
        trust_score = float(confidence * 100.0)

        # Explanation: feature importances aggregated back to original feature names
        explanation = {"feature_importances": {}}
        try:
            clf = self.pipeline.named_steps["clf"]
            importances = clf.feature_importances_
            # try to get transformed feature names from preprocessor
            preproc = self.pipeline.named_steps.get("preproc")
            feat_names = None
            if preproc is not None:
                try:
                    feat_names = preproc.get_feature_names_out()
                except Exception:
                    feat_names = None
            if feat_names is not None and len(importances) == len(feat_names):
                explanation["feature_importances"] = dict(sorted(
                    zip(feat_names.tolist(), importances.tolist()), key=lambda x: x[1], reverse=True
                ))
            else:
                # fallback: provide top-n raw feature importances (no reliable names)
                topn = 10
                vals = sorted(enumerate(importances.tolist()), key=lambda x: x[1], reverse=True)[:topn]
                explanation["feature_importances"] = {f"f_{i}": v for i, v in vals}
        except Exception:
            explanation["feature_importances"] = {}

        return {
            "prediction_label": prediction_label,
            "trust_score": round(trust_score, 2),
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "model_type": "random_forest",
            "model_version": "v1",
        }
