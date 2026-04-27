"""
Evidence Analysis Service for TrustBond
Integrates with report submission to validate evidence content
"""

import os
import json
import cv2
import numpy as np
import io
import requests
import hashlib
import time
import joblib
from collections import Counter
from datetime import datetime, timezone
from PIL import Image, ImageFilter, ImageEnhance
from PIL.ExifTags import TAGS, GPSTAGS
import pytesseract
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
from sqlalchemy.orm import Session
from ultralytics import YOLO
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from shapely.geometry import Point, Polygon

# ── Optional heavy dependencies — imported lazily or at startup ──────────────
try:
    import imagehash as _imagehash
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    _IMAGEHASH_AVAILABLE = False
    logger_init = logging.getLogger(__name__)
    logger_init.warning("imagehash not installed — perceptual hash duplicate detection disabled")

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    import torch as _torch
    _SBERT_AVAILABLE = True
except ImportError:
    _SBERT_AVAILABLE = False

try:
    import xgboost as xgb
    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class EvidenceAnalysis:
    """Results of evidence analysis with advanced features"""
    # Basic Analysis
    has_people: bool = False
    people_count: int = 0
    is_blurry: bool = False
    blur_score: float = 0.0
    brightness: float = 0.0
    has_text: bool = False
    extracted_text: str = ""
    detected_objects: List[str] = field(default_factory=list)
    yolo_object_counts: Dict[str, int] = field(default_factory=dict)
    yolo_presence_flags: Dict[str, bool] = field(default_factory=dict)
    scene_type: str = ""
    file_size: int = 0
    resolution: Tuple[int, int] = (0, 0)
    exif_complete: bool = False
    confidence_score: float = 0.0
    
    # Action Recognition
    detected_actions: List[str] = field(default_factory=list)
    action_confidence: float = 0.0
    motion_intensity: float = 0.0
    
    # Scene Context Analysis
    is_indoor: bool = False
    lighting_condition: str = ""  # day, night, artificial
    weather_condition: str = ""
    scene_confidence: float = 0.0
    
    # Temporal Analysis
    exif_timestamp: Optional[datetime] = None
    timestamp_valid: bool = False
    location_consistent: bool = True
    evidence_sequence_valid: bool = True
    
    # Face Detection & Privacy
    faces_detected: int = 0
    face_locations: List[Tuple[int, int, int, int]] = field(default_factory=list)
    privacy_blurred: bool = False
    
    # Violence Detection
    violence_detected: bool = False
    violence_confidence: float = 0.0
    weapons_detected: List[str] = field(default_factory=list)
    aggressive_poses: int = 0
    
    # Multi-Modal Analysis
    text_object_correlation: float = 0.0
    audio_evidence_available: bool = False
    cross_modal_consistency: float = 0.0
    
    # Quality Scoring
    quality_score: float = 0.0
    technical_quality: float = 0.0
    content_quality: float = 0.0
    authenticity_score: float = 0.0
    
    # Anomaly Detection
    is_anomalous: bool = False
    anomaly_score: float = 0.0
    anomaly_risk_score: float = 0.0
    anomaly_reasons: List[str] = field(default_factory=list)
    
    # Evidence Chain
    evidence_hash: str = ""
    tamper_detected: bool = False
    chain_valid: bool = True
    
    # Real-Time Analysis
    real_time_confidence: float = 0.0
    progressive_validation: List[float] = field(default_factory=list)
    early_false_positive_detected: bool = False
    
    # Predictive Hotspot Mapping
    hotspot_prediction: float = 0.0
    incident_probability: float = 0.0
    resource_allocation_score: float = 0.0
    
    # Cross-Reference Analysis
    similar_reports_count: int = 0
    location_cluster_id: Optional[str] = None
    time_pattern_match: bool = False
    serial_incident_detected: bool = False
    
    # Automated Report Generation
    auto_summary: str = ""
    key_points: List[str] = field(default_factory=list)
    timeline_generated: bool = False
    officer_briefing: str = ""
    
    # Document Forgery Detection
    document_forgery_detected: bool = False
    forgery_confidence: float = 0.0
    forgery_indicators: List[str] = field(default_factory=list)
    document_type: str = ""

    # LLaVA + YOLO Combined Analysis
    llava_scene_description: str = ""
    llava_activities: List[str] = field(default_factory=list)
    llava_environment: str = ""
    llava_interactions: List[str] = field(default_factory=list)
    llava_scene_label: str = ""
    llava_activity_scores: Dict[str, float] = field(default_factory=dict)
    llava_environment_label: str = ""
    yolo_llava_consistency: float = 0.0   # 0.0–1.0; 1.0 = fully consistent
    combined_analysis: str = ""           # final structured narrative

    # Hard Rule Gates
    location_gate_passed: bool = True
    location_gate_reason: str = ""
    originality_gate_passed: bool = True
    originality_gate_issues: List[str] = field(default_factory=list)
    hash_duplicate_detected: bool = False
    screenshot_detected: bool = False
    exif_consistent: bool = True

    # Text Semantic Understanding
    text_similarity_score: float = 0.0         # desc ↔ incident-type anchor
    incident_type_mismatch: bool = False
    semantic_match_score: float = 0.0          # combined tri-way semantic score
    desc_vs_llava_similarity: float = 0.0      # desc ↔ LLaVA scene description
    llava_vs_type_similarity: float = 0.0      # LLaVA scene ↔ incident-type anchor

    # YOLO ML features (structured, not raw names)
    yolo_feature_score: float = 0.0
    yolo_person_present: bool = False
    yolo_vehicle_present: bool = False
    yolo_weapon_present: bool = False
    yolo_high_risk_objects: List[str] = field(default_factory=list)
    yolo_object_diversity: float = 0.0
    yolo_obj_match_rate: float = 0.0

    # LLaVA ML features (structured)
    llava_feature_score: float = 0.0
    llava_violence_activity_score: float = 0.0
    llava_theft_activity_score: float = 0.0
    llava_suspicious_activity_score: float = 0.0
    llava_interaction_complexity: float = 0.0
    llava_incident_indicator_count: int = 0

    # Rule-based score
    rule_based_score: float = 0.0
    evidence_quality_score: float = 0.0        # alias kept in sync with quality_score
    anomaly_risk_score: float = 0.0            # alias kept in sync with anomaly_score

    # YOLO richer feature storage
    yolo_object_counts: Dict = field(default_factory=dict)    # {category_name: count}
    yolo_presence_flags: Dict = field(default_factory=dict)   # {category_name: 0|1}

    # LLaVA richer feature storage
    llava_activity_scores: Dict = field(default_factory=dict) # {category: score}
    llava_scene_label: str = ""                # normalised scene label from LLaVA rules
    llava_environment_label: str = ""          # normalised environment label

    # Incident Decision Engine (XGBoost fusion) — structured output
    decision_label: str = ""                   # REAL | SUSPICIOUS | REJECTED | UNDER_REVIEW
    decision_trust_score: float = 0.0
    xgboost_score: float = 0.0                 # raw XGBoost winning-class probability
    xgboost_probabilities: Dict = field(default_factory=dict)
    decision_reasoning: str = ""
    decision_breakdown: Dict = field(default_factory=dict)
    final_verdict_reason: str = ""             # short one-sentence explanation

class EvidenceAnalysisService:
    """Evidence analysis service for validating incident evidence"""
    
    def __init__(self):
        # Load validation rules from JSON file if it exists
        self.validation_rules = self._load_validation_rules()
        
        # Initialize YOLOv8n model (smallest model - 6MB)
        try:
            self.yolo_model = YOLO('yolov8n.pt')  # Nano version - smallest, fastest
            logger.info("YOLOv8n model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None
        
        # Initialize face detection cascade
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("Face detection cascade loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load face cascade: {e}")
            self.face_cascade = None
        
        # Initialize anomaly detection model
        try:
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.scaler = StandardScaler()
            self.anomaly_trained = False
            logger.info("Anomaly detection model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize anomaly detector: {e}")
            self.anomaly_detector = None
        
        # Initialize evidence chain storage
        self.evidence_chain = {}

        # LLaVA via Ollama — configurable endpoint
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.llava_model = os.getenv("LLAVA_MODEL", "llava:7b")

        # ── Musanze district boundary (GIS polygon, WGS84) ──────────────────
        # Approximate polygon covering Musanze district, Northern Province, Rwanda.
        # lon, lat order for shapely.
        _musanze_coords = [
            (29.4700, -1.2200),   # NW corner
            (29.7200, -1.2200),   # N edge
            (29.9800, -1.3500),   # NE
            (29.9800, -1.6000),   # SE
            (29.7500, -1.7200),   # S
            (29.4700, -1.6800),   # SW
            (29.3500, -1.5000),   # W
            (29.3500, -1.3200),   # NW lower
            (29.4700, -1.2200),   # close
        ]
        self.musanze_polygon = Polygon(_musanze_coords)

        # ── Perceptual hash store (report_id → hash) ────────────────────────
        self._phash_store: Dict[str, Any] = {}

        # ── Sentence transformer for text semantic matching ──────────────────
        self.text_model = None
        if _SBERT_AVAILABLE:
            _model_name = os.getenv(
                "TEXT_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
            )
            try:
                self.text_model = _SentenceTransformer(_model_name)
                logger.info(f"Text embedding model loaded: {_model_name}")
            except Exception as _e:
                logger.warning(f"Could not load text model '{_model_name}': {_e}")

        # Pre-computed anchor phrases per incident type (Kinyarwanda + English)
        self._incident_anchors: Dict[int, str] = {
            1:  "theft robbery stealing money phone bag wallet pickpocket stolen",
            2:  "assault attack fight beating hitting punching weapon injury blood panga",
            3:  "vandalism broken graffiti property destruction damaged spray paint",
            4:  "suspicious lurking watching hiding unusual behaviour loitering",
            5:  "domestic violence abuse household woman child husband wife beating",
            6:  "drugs narcotics selling using cannabis heroin youth paraphernalia",
            7:  "fraud scam deception mobile money fake document trickery",
            8:  "harassment threats stalking intimidation repeated following",
            9:  "traffic accident collision road vehicle crash speeding",
        }
        # Cache anchor embeddings so they are computed only once
        self._anchor_embeddings: Dict[int, Any] = {}

        # ── XGBoost fusion model ─────────────────────────────────────────────
        self.xgb_model = None
        self.xgb_label_map = {0: "REAL", 1: "SUSPICIOUS", 2: "REJECTED"}
        if _XGB_AVAILABLE:
            _model_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "models", "decision_model.ubj"
            )
            if os.path.exists(_model_path):
                try:
                    self.xgb_model = xgb.XGBClassifier()
                    self.xgb_model.load_model(_model_path)
                    logger.info(f"XGBoost decision model loaded from {_model_path}")
                except Exception as _e:
                    logger.warning(f"Failed to load XGBoost model: {_e}")
        
        # Rwanda-specific object mapping (custom detection)
        self.rwanda_objects = {
            # Traditional weapons
            'panga': {'yolo_classes': [42, 101], 'color_range': [(0, 100, 100), (10, 255, 255)], 'shape': 'elongated'},
            'machete': {'yolo_classes': [42, 101], 'color_range': [(0, 100, 100), (15, 255, 255)], 'shape': 'curved'},
            'traditional_knife': {'yolo_classes': [42, 76], 'color_range': [(10, 50, 50), (25, 255, 255)], 'shape': 'pointed'},
            
            # Local currency
            'rwf_note': {'yolo_classes': [84], 'color_range': [(20, 50, 50), (40, 255, 255)], 'shape': 'rectangular'},
            'mobile_money': {'yolo_classes': [67, 62], 'color_range': [(100, 50, 50), (130, 255, 255)], 'shape': 'screen'},
            
            # Rwandan phone models (common brands)
            'tecno_phone': {'yolo_classes': [67], 'color_range': [(0, 0, 50), (180, 255, 255)], 'shape': 'rectangular'},
            'itel_phone': {'yolo_classes': [67], 'color_range': [(0, 0, 50), (180, 255, 255)], 'shape': 'rectangular'},
            'samsung_phone': {'yolo_classes': [67], 'color_range': [(0, 0, 50), (180, 255, 255)], 'shape': 'rectangular'},
            
            # Traditional clothing
            'kitenge': {'yolo_classes': [27, 28], 'color_range': [(0, 50, 50), (180, 255, 255)], 'pattern': 'colorful'},
            'mushanana': {'yolo_classes': [27], 'color_range': [(0, 0, 50), (180, 255, 255)], 'shape': 'flowing'},
            
            # Local vehicles
            'motorcycle_taxi': {'yolo_classes': [3], 'color_range': [(0, 0, 50), (180, 255, 255)], 'context': 'street'},
            'bicycle_taxi': {'yolo_classes': [1], 'color_range': [(0, 0, 50), (180, 255, 255)], 'context': 'street'},
            
            # Market specific items
            'market_stall': {'yolo_classes': [55, 59], 'color_range': [(0, 0, 50), (180, 255, 255)], 'context': 'market'},
            'local_produce': {'yolo_classes': [52, 54], 'color_range': [(20, 100, 50), (80, 255, 255)], 'context': 'market'},
        }
        
        # Legacy defaults (used only if JSON rules missing).
        self.enhanced_rules = {
            1: {'expected_objects': ['person', 'cell phone', 'handbag', 'backpack', 'money'], 'expected_actions': ['running', 'grabbing', 'taking', 'struggling'], 'expected_scenes': ['market', 'street', 'shop'], 'keywords': ['stole', 'stolen', 'thief', 'theft', 'robbed'], 'weight': 1.2},
            2: {'expected_objects': ['person', 'knife', 'blood', 'injury'], 'expected_actions': ['fighting', 'hitting', 'attacking', 'struggling'], 'expected_scenes': ['street', 'public', 'bar'], 'keywords': ['attack', 'assault', 'fight', 'violent', 'injured'], 'weight': 1.6},
            3: {'expected_objects': ['structure', 'vehicle', 'broken', 'damaged'], 'expected_actions': ['breaking', 'destroying', 'painting'], 'expected_scenes': ['wall', 'building', 'street'], 'keywords': ['vandalism', 'broken', 'damaged', 'graffiti'], 'weight': 1.1},
            4: {'expected_objects': ['person', 'vehicle'], 'expected_actions': ['lurking', 'watching', 'hiding', 'following'], 'expected_scenes': ['street', 'building', 'night'], 'keywords': ['suspicious', 'strange', 'unusual', 'lurking'], 'weight': 1.0},
            5: {'expected_objects': ['person', 'chair', 'couch', 'bed'], 'expected_actions': ['fighting', 'hitting', 'struggling'], 'expected_scenes': ['home', 'house', 'indoor'], 'keywords': ['domestic', 'abuse', 'husband', 'wife', 'partner'], 'weight': 1.7},
            6: {'expected_objects': ['person', 'bottle'], 'expected_actions': ['lurking', 'watching'], 'expected_scenes': ['street', 'night'], 'keywords': ['drug', 'drugs', 'dealer', 'selling', 'using'], 'weight': 1.4},
            7: {'expected_objects': ['cell phone', 'mobile_money', 'rwf_note', 'laptop'], 'expected_actions': ['taking'], 'expected_scenes': ['market', 'shop', 'public'], 'keywords': ['fraud', 'scam', 'mobile money', 'otp', 'pin'], 'weight': 1.3},
            8: {'expected_objects': ['person'], 'expected_actions': ['following', 'watching', 'lurking'], 'expected_scenes': ['street', 'public', 'night'], 'keywords': ['harass', 'harassment', 'threat', 'stalking'], 'weight': 1.2},
            9: {'expected_objects': ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'], 'expected_actions': ['running'], 'expected_scenes': ['road', 'street', 'intersection'], 'keywords': ['accident', 'crash', 'collision', 'traffic', 'road'], 'weight': 1.0},
        }
    
    def _load_validation_rules(self) -> Dict:
        """Load validation rules from JSON file if available"""
        try:
            rules_path = os.path.join(os.path.dirname(__file__), '..', '..', 'evidence_validation_rules.json')
            if os.path.exists(rules_path):
                with open(rules_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load validation rules: {e}")
        return {}

    def _get_rules_for_incident(self, incident_type_id: int) -> Dict[str, Any]:
        """
        Return merged rules for an incident type.
        Prefers JSON file (`backend/evidence_validation_rules.json`) when present.
        """
        # JSON stores keys as strings
        raw = None
        try:
            raw = (self.validation_rules or {}).get(str(int(incident_type_id)))
        except Exception:
            raw = None
        if isinstance(raw, dict):
            # Normalize: some files may store `rule` at top-level.
            evidence_rules = raw.get("evidence_rules") if isinstance(raw.get("evidence_rules"), dict) else {}
            rule = evidence_rules.get("rule") if isinstance(evidence_rules.get("rule"), dict) else raw.get("rule", {})
            return {
                "incident_name": raw.get("incident_name"),
                "severity": raw.get("severity"),
                "allow_no_evidence": bool(raw.get("allow_no_evidence", True)),
                "text_rules": raw.get("text_rules") if isinstance(raw.get("text_rules"), dict) else {},
                "evidence_rules": {
                    "allowed_media_types": evidence_rules.get("allowed_media_types", ["photo", "video", "audio"]),
                    "recommended_media_types": evidence_rules.get("recommended_media_types", []),
                    "min_evidence_count_for_auto_verify": evidence_rules.get("min_evidence_count_for_auto_verify", 1),
                    "rule": rule if isinstance(rule, dict) else {},
                },
            }
        # Legacy fallback
        legacy = self.enhanced_rules.get(int(incident_type_id), {}) if incident_type_id else {}
        return {
            "incident_name": None,
            "severity": legacy.get("weight"),
            "allow_no_evidence": True,
            "text_rules": {},
            "evidence_rules": {
                "allowed_media_types": ["photo", "video", "audio"],
                "recommended_media_types": [],
                "min_evidence_count_for_auto_verify": 1,
                "rule": legacy,
            },
        }

    def analyze_video_from_url(self, video_url: str, *, sample_frames: int = 5) -> EvidenceAnalysis:
        """
        Lightweight video analysis:
        - Download video
        - Sample a few frames
        - Run the same per-frame checks we use for images (YOLO objects + basic quality)
        """
        analysis = EvidenceAnalysis()
        try:
            response = requests.get(video_url, timeout=15)
            response.raise_for_status()
            video_bytes = response.content
            if not video_bytes:
                return analysis

            # Write to a temp file for OpenCV VideoCapture
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(video_bytes)
                tmp.flush()
                cap = cv2.VideoCapture(tmp.name)
                if not cap.isOpened():
                    return analysis

                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                if frame_count <= 0:
                    # Still try reading first frame
                    frame_count = 1

                picks = []
                if sample_frames <= 1 or frame_count == 1:
                    picks = [0]
                else:
                    step = max(1, frame_count // sample_frames)
                    picks = list(range(0, min(frame_count, step * sample_frames), step))

                all_objects: set[str] = set()
                people_any = False
                people_max = 0
                blur_scores: list[float] = []
                brightness_scores: list[float] = []

                for idx in picks:
                    try:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                        ok, frame = cap.read()
                        if not ok or frame is None:
                            continue
                        # Basic per-frame stats
                        has_people, people_count = self._detect_people(frame)
                        people_any = people_any or has_people
                        people_max = max(people_max, int(people_count or 0))
                        is_blurry, blur_score = self._detect_blur(frame)
                        blur_scores.append(float(blur_score or 0.0))
                        brightness_scores.append(float(self._analyze_brightness(frame) or 0.0))

                        objs = self._detect_objects_with_yolo(frame)
                        for o in objs or []:
                            all_objects.add(str(o))
                    except Exception:
                        continue

                analysis.detected_objects = sorted(all_objects)
                analysis.has_people = bool(people_any)
                analysis.people_count = int(people_max)
                if blur_scores:
                    analysis.blur_score = float(sum(blur_scores) / len(blur_scores))
                    analysis.is_blurry = analysis.blur_score < 100.0  # keep same semantics as image method
                if brightness_scores:
                    analysis.brightness = float(sum(brightness_scores) / len(brightness_scores))

                # Estimate confidence from "content richness"
                # (video has no EXIF; keep it conservative)
                base = 0.35
                if analysis.has_people:
                    base += 0.2
                if analysis.detected_objects and "unknown" not in analysis.detected_objects:
                    base += 0.2
                if analysis.blur_score and analysis.blur_score >= 80:
                    base += 0.15
                analysis.confidence_score = max(0.0, min(1.0, base))
        except Exception as e:
            logger.warning(f"Video analysis failed for URL {video_url}: {e}")
        return analysis

    def analyze_audio_from_url(self, audio_url: str) -> Dict[str, Any]:
        """
        Lightweight audio validation without heavy dependencies:
        - Detect supported WAV via Python stdlib (wave)
        - Compute duration + simple RMS energy + silence ratio
        For non-WAV formats, returns 'unsupported_format' (still stored for review).
        """
        result: Dict[str, Any] = {
            "supported": False,
            "duration_seconds": None,
            "rms": None,
            "silence_ratio": None,
            "issues": [],
        }
        try:
            response = requests.get(audio_url, timeout=15)
            response.raise_for_status()
            data = response.content or b""
            if not data:
                result["issues"].append("empty_audio")
                return result

            # Try WAV parsing
            import wave
            import contextlib
            import tempfile
            import math
            import struct

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(data)
                tmp.flush()
                try:
                    with contextlib.closing(wave.open(tmp.name, "rb")) as wf:
                        n_channels = wf.getnchannels()
                        sampwidth = wf.getsampwidth()
                        framerate = wf.getframerate()
                        n_frames = wf.getnframes()
                        if framerate and n_frames:
                            dur = float(n_frames) / float(framerate)
                        else:
                            dur = 0.0
                        result["supported"] = True
                        result["duration_seconds"] = dur
                        if dur < 1.0:
                            result["issues"].append("audio_too_short")

                        # Read a limited chunk to estimate energy
                        frames = wf.readframes(min(n_frames, framerate * 10))  # up to 10s
                        if sampwidth == 2 and frames:
                            count = len(frames) // 2
                            samples = struct.unpack("<" + "h" * count, frames)
                            if n_channels > 1:
                                # downmix (rough)
                                samples = samples[::n_channels]
                            # RMS
                            mean_sq = sum((s * s for s in samples)) / max(1, len(samples))
                            rms = math.sqrt(mean_sq) / 32768.0
                            result["rms"] = float(rms)
                            # Silence ratio (very rough): abs(sample) < threshold
                            thr = int(32768 * 0.01)
                            silent = sum(1 for s in samples if abs(s) < thr)
                            result["silence_ratio"] = float(silent / max(1, len(samples)))
                            if result["silence_ratio"] is not None and result["silence_ratio"] > 0.92:
                                result["issues"].append("mostly_silence")
                        else:
                            result["issues"].append("audio_energy_unavailable")
                except wave.Error:
                    result["issues"].append("unsupported_format")
        except Exception as e:
            logger.warning(f"Audio analysis failed for URL {audio_url}: {e}")
            result["issues"].append("audio_download_or_parse_failed")
        return result
    
    def analyze_image_from_url(
        self,
        image_url: str,
        incident_type_id: Optional[int] = None,
        description: str = "",
        reported_lat: float = 0.0,
        reported_lon: float = 0.0,
        report_key: str = "",
        historical_trust: float = 0.5,
        community_votes: float = 0.5,
    ) -> EvidenceAnalysis:
        """Analyze image from Cloudinary URL"""
        try:
            # Download image from URL
            import requests
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            raw_bytes = response.content

            # Load image
            image_array = np.frombuffer(raw_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Could not decode image")

            pil_image = Image.open(io.BytesIO(raw_bytes))

            # Perform analysis
            return self._analyze_image_internal(
                image, pil_image,
                reported_lat=reported_lat,
                reported_lon=reported_lon,
                image_bytes=raw_bytes,
                incident_type_id=incident_type_id,
                description=description,
                report_key=report_key,
                historical_trust=historical_trust,
                community_votes=community_votes,
            )
            
        except Exception as e:
            logger.error(f"Error analyzing image from URL {image_url}: {e}")
            return EvidenceAnalysis()
    
    def _analyze_image_internal(self, image: np.ndarray, pil_image: Image.Image,
                           reported_lat: float = 0.0, reported_lon: float = 0.0,
                           reported_time: Optional[datetime] = None,
                           image_bytes: Optional[bytes] = None,
                           incident_type_id: Optional[int] = None,
                           description: str = "",
                           report_key: str = "",
                           historical_trust: float = 0.5,
                           community_votes: float = 0.5) -> EvidenceAnalysis:
        """Advanced internal image analysis method"""
        analysis = EvidenceAnalysis()
        
        # Basic image properties
        analysis.file_size = len(pil_image.tobytes())
        analysis.resolution = pil_image.size
        analysis.exif_complete = self._check_exif_data(pil_image)
        
        # 1. People detection
        analysis.has_people, analysis.people_count = self._detect_people(image)
        
        # 2. Blur detection
        analysis.is_blurry, analysis.blur_score = self._detect_blur(image)
        
        # 3. Brightness analysis
        analysis.brightness = self._analyze_brightness(image)
        
        # 4. Text extraction (OCR)
        analysis.has_text, analysis.extracted_text = self._extract_text(pil_image)
        
        # 5. Object detection (YOLO-powered)
        analysis.detected_objects = self._detect_objects_with_yolo(image)

        # 5.5 LLaVA scene analysis + YOLO–LLaVA merge
        try:
            _img_bytes = image_bytes
            if _img_bytes is None:
                buf = io.BytesIO()
                pil_image.save(buf, format="JPEG", quality=85)
                _img_bytes = buf.getvalue()

            llava_result = self._run_llava_analysis(_img_bytes, incident_type_id)
            merge = self._merge_yolo_and_llava(analysis.detected_objects, llava_result)

            analysis.llava_scene_description = llava_result.get("scene_description", "")
            analysis.llava_activities = llava_result.get("activities", [])
            analysis.llava_environment = llava_result.get("environment", "")
            analysis.llava_interactions = llava_result.get("interactions", [])
            analysis.llava_scene_label = (
                llava_result.get("environment", "") or llava_result.get("scene_description", "")
            )
            analysis.llava_environment_label = llava_result.get("environment", "")
            analysis.llava_incident_indicator_count = len(llava_result.get("incident_indicators", []) or [])
            analysis.yolo_llava_consistency = merge["consistency_score"]
            analysis.combined_analysis = merge["combined_narrative"]

            # Enrich detected_objects with LLaVA-only findings (no duplicates)
            yolo_lower = {o.lower() for o in analysis.detected_objects}
            for obj in llava_result.get("objects", []):
                if obj.lower() not in yolo_lower:
                    analysis.detected_objects.append(obj)
                    yolo_lower.add(obj.lower())

            # Merge LLaVA activities into detected_actions
            existing_actions = {a.lower() for a in analysis.detected_actions}
            for act in llava_result.get("activities", []):
                if act.lower() not in existing_actions:
                    analysis.detected_actions.append(act)
                    existing_actions.add(act.lower())
        except Exception as _llava_exc:
            logger.warning(f"LLaVA integration step failed: {_llava_exc}")

        # 6. Scene classification
        analysis.scene_type = self._classify_scene(image, analysis.detected_objects)
        
        # === ADVANCED FEATURES ===
        
        # 7. Action Recognition
        actions, action_conf, motion_intensity = self._detect_actions_optical_flow(image)
        # Merge optical-flow actions with LLaVA activities (de-duplicate, keep both)
        existing_actions_lower = {a.lower() for a in analysis.detected_actions}
        for act in actions:
            if act.lower() not in existing_actions_lower:
                analysis.detected_actions.append(act)
                existing_actions_lower.add(act.lower())
        analysis.action_confidence = action_conf
        analysis.motion_intensity = motion_intensity
        
        # 8. Scene Context Analysis
        scene_context = self._analyze_scene_context(image, analysis.detected_objects)
        analysis.is_indoor = scene_context['is_indoor']
        analysis.lighting_condition = scene_context['lighting_condition']
        analysis.weather_condition = scene_context['weather_condition']
        analysis.scene_confidence = scene_context['scene_confidence']
        
        # 9. Temporal Analysis
        temporal = self._perform_temporal_analysis(pil_image, reported_lat, reported_lon, reported_time)
        analysis.exif_timestamp = temporal['exif_timestamp']
        analysis.timestamp_valid = temporal['timestamp_valid']
        analysis.location_consistent = temporal['location_consistent']
        analysis.evidence_sequence_valid = temporal['evidence_sequence_valid']
        
        # 10. Face Detection & Privacy Blurring
        faces_count, face_locs, blurred = self._detect_faces_and_blur(image)
        analysis.faces_detected = faces_count
        analysis.face_locations = face_locs
        analysis.privacy_blurred = blurred
        
        # 11. Violence Detection
        violence = self._detect_violence(image, analysis.detected_objects)
        analysis.violence_detected = violence['violence_detected']
        analysis.violence_confidence = violence['violence_confidence']
        analysis.weapons_detected = violence['weapons_detected']
        analysis.aggressive_poses = violence['aggressive_poses']
        
        # 12. Multi-Modal Analysis
        multimodal = self._perform_multimodal_analysis(analysis.detected_objects, analysis.extracted_text)
        analysis.text_object_correlation = multimodal['text_object_correlation']
        analysis.audio_evidence_available = multimodal['audio_evidence_available']
        analysis.cross_modal_consistency = multimodal['cross_modal_consistency']
        
        # 13. Evidence Chain Verification
        chain = self._verify_evidence_chain(pil_image)
        analysis.evidence_hash = chain['evidence_hash']
        analysis.tamper_detected = chain['tamper_detected']
        analysis.chain_valid = chain['chain_valid']
        
        # 14. Quality Scoring
        quality = self._calculate_quality_scores(analysis)
        analysis.quality_score = quality['quality_score']
        analysis.technical_quality = quality['technical_quality']
        analysis.content_quality = quality['content_quality']
        analysis.authenticity_score = quality['authenticity_score']
        analysis.evidence_quality_score = round(
            (
                analysis.quality_score * 0.40 +
                analysis.technical_quality * 0.20 +
                analysis.content_quality * 0.20 +
                analysis.authenticity_score * 0.20
            ),
            3,
        )

        # 15. Anomaly Detection
        anomaly = self._detect_anomalies(analysis)
        analysis.is_anomalous = anomaly['is_anomalous']
        analysis.anomaly_score = anomaly['anomaly_score']
        analysis.anomaly_risk_score = self._normalize_anomaly_score(
            anomaly['anomaly_score'],
            anomaly.get('is_anomalous', False),
        )
        analysis.anomaly_reasons = anomaly['anomaly_reasons']
        
        # === MISSING FEATURES IMPLEMENTATION ===
        
        # 16. Document Forgery Detection
        forgery = self._detect_document_forgery(image, analysis.extracted_text, analysis.detected_objects)
        analysis.document_forgery_detected = forgery['is_forged']
        analysis.forgery_confidence = forgery['forgery_confidence']
        analysis.forgery_indicators = forgery['forgery_indicators']
        analysis.document_type = forgery['document_type']
        
        # 17. Real-Time Analysis
        realtime = self._perform_real_time_analysis(analysis)
        analysis.real_time_confidence = realtime['confidence']
        analysis.progressive_validation = realtime['validation_progression']
        analysis.early_false_positive_detected = realtime['early_false_positive']
        
        # 18. Predictive Hotspot Mapping
        hotspot = self._predict_hotspot_probability(analysis, reported_lat, reported_lon)
        analysis.hotspot_prediction = hotspot['prediction']
        analysis.incident_probability = hotspot['incident_probability']
        analysis.resource_allocation_score = hotspot['resource_score']
        
        # 19. Cross-Reference Analysis
        crossref = self._perform_cross_reference_analysis(analysis, reported_lat, reported_lon)
        analysis.similar_reports_count = crossref['similar_count']
        analysis.location_cluster_id = crossref['cluster_id']
        analysis.time_pattern_match = crossref['time_pattern']
        analysis.serial_incident_detected = crossref['serial_incident']
        
        # 20. Automated Report Generation
        report = self._generate_automated_report(analysis)
        analysis.auto_summary = report['summary']
        analysis.key_points = report['key_points']
        analysis.timeline_generated = report['timeline_generated']
        analysis.officer_briefing = report['briefing']
        
        # Calculate overall confidence (updated with advanced features)
        analysis.confidence_score = self._calculate_advanced_confidence_score(analysis)

        # 21. Hybrid Decision Engine (REAL / SUSPICIOUS / REJECTED / UNDER_REVIEW)
        decision = self._run_decision_engine(
            analysis,
            incident_type_id=incident_type_id,
            description=description,
            reported_lat=reported_lat,
            reported_lon=reported_lon,
            historical_trust=historical_trust,
            community_votes=community_votes,
            report_key=report_key,
            image_bytes=image_bytes,
            pil_image=pil_image,
        )
        analysis.decision_label       = decision["label"]
        analysis.decision_trust_score = decision["trust_score"]
        analysis.decision_reasoning   = decision["reasoning"]
        analysis.decision_breakdown   = decision["breakdown"]

        # Prepend the verdict banner to the officer briefing
        verdict_icons = {"REAL": "✅", "SUSPICIOUS": "⚠️", "REJECTED": "❌", "UNDER_REVIEW": "🔍"}
        icon = verdict_icons.get(decision["label"], "❓")
        bd = decision.get("breakdown", {})
        verdict_banner = (
            f"{icon} VERDICT: {decision['label']}  "
            f"(Trust Score: {decision['trust_score']:.0%}  |  XGBoost: {decision.get('xgboost_score', 0):.0%})\n"
            f"Semantic: {analysis.semantic_match_score:.2f}  "
            f"Rule: {analysis.rule_based_score:.2f}  "
            f"YOLO: {analysis.yolo_feature_score:.2f}  "
            f"LLaVA: {analysis.llava_feature_score:.2f}  "
            f"Quality: {analysis.evidence_quality_score:.2f}  "
            f"Anomaly Risk: {analysis.anomaly_risk_score:.2f}\n"
            f"Reason: {decision.get('final_verdict_reason', '')}\n"
            "─" * 60
        )
        analysis.officer_briefing = verdict_banner + "\n" + analysis.officer_briefing

        return analysis
    
    def _detect_people(self, image: np.ndarray) -> Tuple[bool, int]:
        """Detect people in image using OpenCV"""
        try:
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            boxes, weights = hog.detectMultiScale(image, winStride=(8, 8))
            people_count = len(boxes)
            has_people = people_count > 0
            
            return has_people, people_count
            
        except Exception as e:
            logger.warning(f"People detection failed: {e}")
            return False, 0
    
    def _detect_blur(self, image: np.ndarray) -> Tuple[bool, float]:
        """Detect if image is blurry using Laplacian variance"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            blur_threshold = 100.0
            is_blurry = laplacian_var < blur_threshold
            
            return is_blurry, laplacian_var
            
        except Exception as e:
            logger.warning(f"Blur detection failed: {e}")
            return True, 0.0
    
    def _analyze_brightness(self, image: np.ndarray) -> float:
        """Analyze image brightness"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray) / 255.0
            return brightness
        except Exception as e:
            logger.warning(f"Brightness analysis failed: {e}")
            return 0.5
    
    def _extract_text(self, image: Image.Image) -> Tuple[bool, str]:
        """Extract text from image using OCR"""
        try:
            gray = image.convert('L')
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2.0)
            
            text = pytesseract.image_to_string(enhanced)
            text = text.strip()
            
            has_text = len(text) > 5
            return has_text, text
            
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
            return False, ""
    
    def _detect_objects_with_yolo(self, image: np.ndarray) -> List[str]:
        """Detect objects using YOLOv8n model with Rwanda-specific custom detection"""
        if self.yolo_model is None:
            # Fallback to basic detection if YOLO fails
            return self._detect_basic_objects_fallback(image)
        
        try:
            # Run YOLO inference
            results = self.yolo_model(image, verbose=False)
            
            # Map COCO classes to TrustBond relevant objects
            trustbond_objects = []
            
            # COCO classes relevant to TrustBond incidents
            relevant_classes = {
                0: 'person',           # People detection
                67: 'cell phone',      # Theft evidence
                24: 'handbag',         # Theft evidence  
                28: 'backpack',        # Theft evidence
                39: 'bottle',          # Drug paraphernalia
                42: 'knife',           # Weapon
                43: 'spoon',           # Drug paraphernalia
                44: 'bowl',            # Drug paraphernalia
                45: 'banana',          # Can look like weapons
                46: 'apple',           # Can look like objects
                47: 'sandwich',        # Can look like objects
                48: 'orange',          # Can look like objects
                49: 'broccoli',        # Can look like objects
                50: 'carrot',          # Can look like objects
                51: 'hot dog',         # Can look like objects
                52: 'pizza',           # Can look like objects
                53: 'donut',           # Can look like objects
                54: 'cake',            # Can look like objects
                55: 'chair',           # Domestic violence
                56: 'couch',           # Domestic violence
                57: 'potted plant',    # Indoor objects
                58: 'bed',             # Domestic violence
                59: 'dining table',    # Domestic violence
                60: 'toilet',          # Indoor objects
                61: 'tv',              # Indoor objects
                62: 'laptop',          # Fraud evidence
                63: 'mouse',           # Can look like objects
                64: 'remote',          # Can look like objects
                65: 'keyboard',        # Can look like objects
                66: 'cell phone',      # Theft evidence
                68: 'microwave',       # Indoor objects
                69: 'oven',            # Indoor objects
                70: 'toaster',         # Indoor objects
                71: 'sink',            # Indoor objects
                72: 'refrigerator',    # Indoor objects
                73: 'book',            # Can look like objects
                74: 'clock',           # Indoor objects
                75: 'vase',            # Vandalism target
                76: 'scissors',        # Weapon
                77: 'teddy bear',      # Domestic violence
                78: 'hair drier',      # Can look like weapons
                79: 'toothbrush',      # Can look like objects
                80: 'hair brush',      # Can look like weapons
                81: 'tie',             # Clothing
                82: 'backpack',        # Theft evidence
                84: 'handbag',         # Theft evidence
                85: 'suitcase',        # Theft evidence
                86: 'frisbee',         # Can look like objects
                87: 'skis',            # Can look like weapons
                88: 'snowboard',       # Can look like objects
                89: 'sports ball',     # Can look like objects
                90: 'kite',            # Can look like objects
                91: 'baseball bat',    # Weapon
                92: 'baseball glove',  # Can look like objects
                93: 'skateboard',      # Can look like objects
                94: 'surfboard',       # Can look like objects
                95: 'tennis racket',   # Can look like weapons
                96: 'bottle',          # Drug paraphernalia
                97: 'plate',           # Domestic violence
                98: 'wine glass',      # Domestic violence
                99: 'cup',             # Domestic violence
                100: 'fork',           # Can look like weapons
                101: 'knife',          # Weapon
                102: 'spoon',          # Drug paraphernalia
                103: 'bowl',           # Drug paraphernalia
                104: 'banana',         # Can look like objects
                105: 'apple',          # Can look like objects
                106: 'sandwich',       # Can look like objects
                107: 'orange',         # Can look like objects
                108: 'broccoli',       # Can look like objects
                109: 'carrot',         # Can look like objects
                110: 'hot dog',        # Can look like objects
                111: 'pizza',          # Can look like objects
                112: 'donut',          # Can look like objects
                113: 'cake',           # Can look like objects
                114: 'chair',          # Domestic violence
                115: 'couch',          # Domestic violence
                116: 'potted plant',   # Indoor objects
                117: 'bed',            # Domestic violence
                118: 'dining table',   # Domestic violence
                119: 'toilet',         # Indoor objects
                120: 'tv',             # Indoor objects
                121: 'laptop',         # Fraud evidence
                122: 'mouse',          # Can look like objects
                123: 'remote',         # Can look like objects
                124: 'keyboard',       # Can look like objects
                125: 'cell phone',     # Theft evidence
                126: 'microwave',      # Indoor objects
                127: 'oven',           # Indoor objects
                128: 'toaster',        # Indoor objects
                129: 'sink',           # Indoor objects
                130: 'refrigerator',   # Indoor objects
                131: 'book',           # Can look like objects
                132: 'clock',          # Indoor objects
                133: 'vase',           # Vandalism target
                134: 'scissors',       # Weapon
                135: 'teddy bear',     # Domestic violence
                136: 'hair drier',     # Can look like weapons
                137: 'toothbrush',     # Can look like objects
                138: 'hair brush',     # Can look like weapons
                139: 'tie',            # Clothing
                140: 'backpack',       # Theft evidence
                141: 'handbag',        # Theft evidence
                142: 'suitcase',       # Theft evidence
                143: 'frisbee',        # Can look like objects
                144: 'skis',           # Can look like weapons
                145: 'snowboard',      # Can look like objects
                146: 'sports ball',    # Can look like objects
                147: 'kite',           # Can look like objects
                148: 'baseball bat',   # Weapon
                149: 'baseball glove', # Can look like objects
                150: 'skateboard',     # Can look like objects
                151: 'surfboard',      # Can look like objects
                152: 'tennis racket',  # Can look like weapons
                153: 'bottle',         # Drug paraphernalia
                154: 'plate',          # Domestic violence
                155: 'wine glass',     # Domestic violence
                156: 'cup',            # Domestic violence
                157: 'fork',           # Can look like weapons
                158: 'knife',          # Weapon
                159: 'spoon',          # Drug paraphernalia
                160: 'bowl',           # Drug paraphernalia
                161: 'banana',         # Can look like objects
                162: 'apple',          # Can look like objects
                163: 'sandwich',       # Can look like objects
                164: 'orange',         # Can look like objects
                165: 'broccoli',       # Can look like objects
                166: 'carrot',         # Can look like objects
                167: 'hot dog',        # Can look like objects
                168: 'pizza',          # Can look like objects
                169: 'donut',          # Can look like objects
                170: 'cake',           # Can look like objects
                171: 'chair',          # Domestic violence
                172: 'couch',          # Domestic violence
                173: 'potted plant',   # Indoor objects
                174: 'bed',            # Domestic violence
                175: 'dining table',   # Domestic violence
                176: 'toilet',         # Indoor objects
                177: 'tv',             # Indoor objects
                178: 'laptop',         # Fraud evidence
                179: 'mouse',          # Can look like objects
                180: 'remote',         # Can look like objects
                181: 'keyboard',       # Can look like objects
                182: 'cell phone',     # Theft evidence
            }
            
            # Extract detected objects and apply Rwanda-specific detection
            detected_boxes = []
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls)
                        confidence = float(box.conf)
                        
                        # Only include high-confidence detections
                        if confidence > 0.5:  # 50% confidence threshold
                            if class_id in relevant_classes:
                                object_name = relevant_classes[class_id]
                                if object_name not in trustbond_objects:
                                    trustbond_objects.append(object_name)
                            
                            # Store box info for custom detection
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            detected_boxes.append({
                                'class_id': class_id,
                                'confidence': confidence,
                                'box': (int(x1), int(y1), int(x2), int(y2))
                            })
            
            # Apply Rwanda-specific custom detection
            rwanda_objects = self._detect_rwanda_objects(image, detected_boxes)
            trustbond_objects.extend(rwanda_objects)
            
            # If no relevant objects found, return basic detection
            if not trustbond_objects:
                return self._detect_basic_objects_fallback(image)
            
            return list(set(trustbond_objects))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"YOLO object detection failed: {e}")
            # Fallback to basic detection
            return self._detect_basic_objects_fallback(image)
    
    def _detect_rwanda_objects(self, image: np.ndarray, detected_boxes: List[Dict]) -> List[str]:
        """Detect Rwanda-specific objects using custom algorithms"""
        rwanda_objects = []
        
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            for obj_name, obj_config in self.rwanda_objects.items():
                detected = False
                
                # Check if any YOLO detection matches this object
                for box_info in detected_boxes:
                    if box_info['class_id'] in obj_config['yolo_classes']:
                        x1, y1, x2, y2 = box_info['box']
                        roi = image[y1:y2, x1:x2]
                        roi_hsv = hsv[y1:y2, x1:x2]
                        
                        # Apply color-based detection
                        if 'color_range' in obj_config:
                            lower, upper = obj_config['color_range']
                            mask = cv2.inRange(roi_hsv, np.array(lower), np.array(upper))
                            color_ratio = np.sum(mask > 0) / mask.size
                            
                            if color_ratio > 0.1:  # 10% color coverage
                                detected = True
                        
                        # Apply shape-based detection
                        if detected and 'shape' in obj_config:
                            roi_gray = gray[y1:y2, x1:x2]
                            contours, _ = cv2.findContours(roi_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            
                            if contours:
                                largest_contour = max(contours, key=cv2.contourArea)
                                
                                if obj_config['shape'] == 'elongated':
                                    # Check for elongated shape (panga/machete)
                                    rect = cv2.minAreaRect(largest_contour)
                                    (w, h) = rect[1]
                                    if w > 0 and h > 0:
                                        aspect_ratio = max(w, h) / min(w, h)
                                        if aspect_ratio > 3:  # Very elongated
                                            detected = True
                                
                                elif obj_config['shape'] == 'curved':
                                    # Check for curved shape
                                    perimeter = cv2.arcLength(largest_contour, True)
                                    area = cv2.contourArea(largest_contour)
                                    if perimeter > 0:
                                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                                        if 0.3 < circularity < 0.8:  # Semi-circular
                                            detected = True
                        
                        # Apply pattern detection
                        if detected and 'pattern' in obj_config:
                            if obj_config['pattern'] == 'colorful':
                                # Check for colorful patterns (kitenge)
                                unique_colors = len(np.unique(roi_hsv.reshape(-1, 3), axis=0))
                                if unique_colors > 50:  # Many different colors
                                    detected = True
                        
                        # Apply context detection
                        if detected and 'context' in obj_config:
                            # This would require scene analysis - simplified for now
                            if obj_config['context'] in ['market', 'street']:
                                detected = True  # Assume context matches
                
                if detected:
                    rwanda_objects.append(obj_name)
                    logger.info(f"Rwanda-specific object detected: {obj_name}")
            
        except Exception as e:
            logger.warning(f"Rwanda object detection failed: {e}")
        
        return rwanda_objects
    
    def _detect_basic_objects_fallback(self, image: np.ndarray) -> List[str]:
        """Fallback basic object detection using OpenCV"""
        objects = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple people detection using OpenCV HOG as fallback
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            boxes, _ = hog.detectMultiScale(image, winStride=(8, 8))
            
            if len(boxes) > 0:
                objects.append('person')
            
            # Basic edge detection for structures
            edges = cv2.Canny(gray, 50, 150)
            edge_ratio = np.sum(edges > 0) / edges.size
            
            if edge_ratio > 0.05:
                objects.append('structure')
            
            if len(objects) == 0:
                objects.append('unknown')
                
        except Exception as e:
            logger.warning(f"Fallback object detection failed: {e}")
            objects.append('unknown')
        
        return objects
    
    def _detect_actions_optical_flow(self, image: np.ndarray) -> Tuple[List[str], float, float]:
        """Detect actions using optical flow analysis"""
        actions = []
        confidence = 0.0
        motion_intensity = 0.0
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate optical flow (simplified for single image)
            # In real implementation, this would need video frames
            # For now, we'll use edge detection and contour analysis as proxy
            
            # Detect edges and motion-like patterns
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze contour patterns for action indicators
            large_contours = [c for c in contours if cv2.contourArea(c) > 1000]
            motion_intensity = len(large_contours) / max(len(contours), 1)
            
            # Detect running/movement patterns
            if motion_intensity > 0.3:
                actions.append('running')
                confidence += 0.3
            
            # Detect struggling/fighting patterns (irregular shapes)
            irregular_shapes = 0
            for contour in large_contours:
                perimeter = cv2.arcLength(contour, True)
                area = cv2.contourArea(contour)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity < 0.3:  # Irregular shapes
                        irregular_shapes += 1
            
            if irregular_shapes > len(large_contours) * 0.5:
                actions.append('fighting')
                confidence += 0.4
            
            # Detect taking/grabbing (hand-like shapes)
            hand_like_shapes = 0
            for contour in large_contours:
                area = cv2.contourArea(contour)
                if 500 < area < 2000:  # Hand-sized regions
                    hand_like_shapes += 1
            
            if hand_like_shapes > 0:
                actions.append('grabbing')
                confidence += 0.3
            
            confidence = min(confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"Action detection failed: {e}")
        
        return actions, confidence, motion_intensity
    
    def _analyze_scene_context(self, image: np.ndarray, detected_objects: List[str]) -> Dict:
        """Advanced scene context analysis"""
        context = {
            'is_indoor': False,
            'lighting_condition': '',
            'weather_condition': '',
            'scene_confidence': 0.0
        }
        
        try:
            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Lighting analysis
            brightness = np.mean(gray) / 255.0
            
            if brightness > 0.7:
                context['lighting_condition'] = 'day'
            elif brightness < 0.3:
                context['lighting_condition'] = 'night'
            else:
                context['lighting_condition'] = 'artificial'
            
            # Indoor/outdoor detection
            # Check for indoor indicators
            indoor_objects = ['chair', 'couch', 'bed', 'table', 'tv', 'laptop', 'refrigerator']
            outdoor_objects = ['car', 'truck', 'bus', 'motorcycle']
            
            indoor_score = sum(1 for obj in indoor_objects if obj in detected_objects)
            outdoor_score = sum(1 for obj in outdoor_objects if obj in detected_objects)
            
            # Analyze texture patterns (walls vs sky)
            texture_variance = np.var(gray)
            
            if indoor_score > outdoor_score or texture_variance < 1000:
                context['is_indoor'] = True
            else:
                context['is_indoor'] = False
            
            # Weather detection (basic)
            if brightness < 0.4 and not context['is_indoor']:
                # Check for rain patterns (vertical streaks)
                edges = cv2.Canny(gray, 50, 150)
                vertical_lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                               minLineLength=50, maxLineGap=10)
                
                if vertical_lines is not None:
                    vertical_count = sum(1 for line in vertical_lines 
                                       if abs(line[0][3] - line[0][1]) > abs(line[0][2] - line[0][0]))
                    if vertical_count > len(vertical_lines) * 0.6:
                        context['weather_condition'] = 'rainy'
            
            # Calculate scene confidence
            context['scene_confidence'] = max(indoor_score, outdoor_score) / max(len(detected_objects), 1)
            
        except Exception as e:
            logger.warning(f"Scene context analysis failed: {e}")
        
        return context
    
    def _perform_temporal_analysis(self, image: Image.Image, reported_lat: float, 
                                 reported_lon: float, reported_time: Optional[datetime] = None) -> Dict:
        """Temporal analysis of evidence"""
        temporal = {
            'exif_timestamp': None,
            'timestamp_valid': False,
            'location_consistent': True,
            'evidence_sequence_valid': True
        }
        
        try:
            # Extract EXIF timestamp
            exif = image._getexif()
            if exif:
                # Look for DateTimeOriginal tag
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        try:
                            temporal['exif_timestamp'] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            
                            # Validate timestamp
                            if reported_time:
                                time_diff = abs((temporal['exif_timestamp'] - reported_time).total_seconds())
                                temporal['timestamp_valid'] = time_diff < 3600  # Within 1 hour
                            
                        except ValueError:
                            pass
                        break
            
            # Location consistency (would need GPS data from EXIF for full implementation)
            # For now, we'll assume consistency
            
            # Evidence sequence validation (would need multiple evidence files)
            # For now, we'll assume valid
            
        except Exception as e:
            logger.warning(f"Temporal analysis failed: {e}")
        
        return temporal
    
    def _detect_faces_and_blur(self, image: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]], bool]:
        """Detect faces and apply privacy blurring"""
        faces_detected = 0
        face_locations = []
        privacy_blurred = False
        
        if self.face_cascade is None:
            return faces_detected, face_locations, privacy_blurred
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            faces_detected = len(faces)
            face_locations = [(x, y, x+w, y+h) for (x, y, w, h) in faces]
            
            # Apply privacy blurring
            if faces_detected > 0:
                for (x, y, w, h) in faces:
                    # Blur the face region
                    face_region = image[y:y+h, x:x+w]
                    blurred_face = cv2.GaussianBlur(face_region, (99, 99), 30)
                    image[y:y+h, x:x+w] = blurred_face
                
                privacy_blurred = True
                logger.info(f"Applied privacy blur to {faces_detected} face(s)")
            
        except Exception as e:
            logger.warning(f"Face detection/blurring failed: {e}")
        
        return faces_detected, face_locations, privacy_blurred
    
    def _detect_violence(self, image: np.ndarray, detected_objects: List[str]) -> Dict:
        """Violence detection using object and pose analysis"""
        violence = {
            'violence_detected': False,
            'violence_confidence': 0.0,
            'weapons_detected': [],
            'aggressive_poses': 0
        }
        
        try:
            # Check for weapons
            weapon_objects = ['knife', 'scissors', 'baseball bat', 'tennis racket']
            violence['weapons_detected'] = [obj for obj in weapon_objects if obj in detected_objects]
            
            if violence['weapons_detected']:
                violence['violence_confidence'] += 0.5
                violence['violence_detected'] = True
            
            # Analyze for aggressive poses (simplified)
            # In real implementation, this would use pose estimation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Look for aggressive patterns (sharp angles, irregular shapes)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            aggressive_count = 0
            for contour in contours:
                if cv2.contourArea(contour) > 1000:
                    # Approximate contour to polygon
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Sharp angles might indicate aggressive poses
                    if len(approx) > 6:  # Complex shapes
                        aggressive_count += 1
            
            violence['aggressive_poses'] = aggressive_count
            
            if aggressive_count > 3:
                violence['violence_confidence'] += 0.3
                violence['violence_detected'] = True
            
            violence['violence_confidence'] = min(violence['violence_confidence'], 1.0)
            
        except Exception as e:
            logger.warning(f"Violence detection failed: {e}")
        
        return violence
    
    def _detect_document_forgery(self, image: np.ndarray, extracted_text: str, detected_objects: List[str]) -> Dict:
        """Document forgery detection for fraud/scam incidents"""
        forgery = {
            'is_forged': False,
            'forgery_confidence': 0.0,
            'forgery_indicators': [],
            'document_type': '',
            'authenticity_score': 0.0
        }
        
        try:
            # Check for mobile money screenshots
            if 'mobile_money' in detected_objects or 'cell phone' in detected_objects:
                forgery['document_type'] = 'mobile_money_screenshot'
                
                # Analyze for common mobile money forgery indicators
                text_lower = extracted_text.lower()
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    'fake', 'edited', 'photoshop', 'screenshot',
                    'test', 'demo', 'sample', 'mockup',
                    'frw', 'rwf', '000', '999'  # Fake amounts
                ]
                
                pattern_matches = 0
                for pattern in suspicious_patterns:
                    if pattern in text_lower:
                        pattern_matches += 1
                        forgery['forgery_indicators'].append(f'Suspicious pattern: {pattern}')
                
                # Check for inconsistent formatting
                if 'frw' in text_lower or 'rwf' in text_lower:
                    # Look for inconsistent currency formatting
                    import re
                    amounts = re.findall(r'\d+', text_lower)
                    if amounts:
                        for amount in amounts:
                            if len(amount) > 9 or len(amount) < 3:  # Unusual amount lengths
                                forgery['forgery_indicators'].append(f'Suspicious amount: {amount}')
                                pattern_matches += 1
                
                # Image analysis for screenshot artifacts
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                
                # Look for digital artifacts common in screenshots
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                perfect_rectangles = 0
                
                for contour in contours:
                    if cv2.contourArea(contour) > 1000:
                        # Check if contour is a perfect rectangle (common in UI elements)
                        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                        if len(approx) == 4:
                            perfect_rectangles += 1
                
                if perfect_rectangles > 5:  # Too many perfect rectangles suggests screenshot
                    forgery['forgery_indicators'].append('Digital UI elements detected')
                    pattern_matches += 1
                
                # Calculate forgery confidence
                forgery['forgery_confidence'] = min(pattern_matches * 0.2, 1.0)
                forgery['is_forged'] = forgery['forgery_confidence'] > 0.6
                forgery['authenticity_score'] = 1.0 - forgery['forgery_confidence']
            
            # Check for document tampering
            elif 'laptop' in detected_objects or 'cell phone' in detected_objects:
                forgery['document_type'] = 'digital_document'
                
                # Analyze for document tampering
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                
                # Check for inconsistent lighting (possible editing)
                h, s, v = cv2.split(hsv)
                lighting_variance = np.var(v)
                
                if lighting_variance > 10000:  # High variance suggests editing
                    forgery['forgery_indicators'].append('Inconsistent lighting detected')
                    forgery['forgery_confidence'] += 0.3
                
                # Check for copy-paste artifacts
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Look for repeated patterns (copy-paste)
                template_size = 50
                h, w = gray.shape
                
                for y in range(0, h - template_size, template_size):
                    for x in range(0, w - template_size, template_size):
                        template = gray[y:y+template_size, x:x+template_size]
                        
                        # Search for similar templates
                        res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                        matches = np.where(res >= 0.9)
                        
                        if len(matches[0]) > 2:  # Found multiple similar areas
                            forgery['forgery_indicators'].append('Copy-paste artifacts detected')
                            forgery['forgery_confidence'] += 0.4
                            break
                
                forgery['is_forged'] = forgery['forgery_confidence'] > 0.5
                forgery['authenticity_score'] = 1.0 - forgery['forgery_confidence']
            
            # QR Code validation
            qr_patterns = re.findall(r'[A-Z0-9]{10,}', extracted_text)
            if qr_patterns:
                forgery['forgery_indicators'].append('QR code patterns detected')
                forgery['forgery_confidence'] += 0.1
                
                # Basic QR code validation (simplified)
                for pattern in qr_patterns:
                    if len(pattern) > 50:  # Unusually long QR code
                        forgery['forgery_indicators'].append('Suspicious QR code length')
                        forgery['forgery_confidence'] += 0.2
            
            # Cap confidence at 1.0
            forgery['forgery_confidence'] = min(forgery['forgery_confidence'], 1.0)
            
        except Exception as e:
            logger.warning(f"Document forgery detection failed: {e}")
        
        return forgery
    
    def _perform_multimodal_analysis(self, detected_objects: List[str], extracted_text: str) -> Dict:
        """Multi-modal analysis correlating text and visual evidence"""
        multimodal = {
            'text_object_correlation': 0.0,
            'audio_evidence_available': False,
            'cross_modal_consistency': 0.0
        }
        
        try:
            # Text-object correlation
            text_lower = extracted_text.lower()
            
            # Check for correlation between detected objects and text
            object_text_matches = 0
            for obj in detected_objects:
                if obj.replace('_', ' ') in text_lower:
                    object_text_matches += 1
            
            if detected_objects:
                multimodal['text_object_correlation'] = object_text_matches / len(detected_objects)
            
            # Audio evidence (placeholder - would need audio file analysis)
            multimodal['audio_evidence_available'] = False
            
            # Cross-modal consistency
            # High correlation between text and objects indicates consistency
            multimodal['cross_modal_consistency'] = multimodal['text_object_correlation']
            
        except Exception as e:
            logger.warning(f"Multi-modal analysis failed: {e}")
        
        return multimodal
    
    def _calculate_quality_scores(self, analysis: 'EvidenceAnalysis') -> Dict:
        """Calculate comprehensive quality scores"""
        quality = {
            'quality_score': 0.0,
            'technical_quality': 0.0,
            'content_quality': 0.0,
            'authenticity_score': 0.0
        }
        
        try:
            # Technical quality (blur, resolution, brightness)
            tech_score = 0.0
            
            # Blur score (inverse - higher is better)
            if not analysis.is_blurry:
                tech_score += 0.3
            
            # Resolution check
            if analysis.resolution[0] >= 1280 and analysis.resolution[1] >= 720:
                tech_score += 0.3
            elif analysis.resolution[0] >= 640 and analysis.resolution[1] >= 480:
                tech_score += 0.2
            
            # Brightness check
            if 0.3 <= analysis.brightness <= 0.8:
                tech_score += 0.2
            
            # EXIF completeness
            if analysis.exif_complete:
                tech_score += 0.2
            
            quality['technical_quality'] = tech_score
            
            # Content quality (objects, actions, text)
            content_score = 0.0
            
            # Object detection quality
            if analysis.detected_objects and 'unknown' not in analysis.detected_objects:
                content_score += 0.3
            
            # Action detection quality
            if analysis.detected_actions:
                content_score += 0.2
            
            # Text extraction quality
            if analysis.has_text and len(analysis.extracted_text) > 10:
                content_score += 0.2
            
            # Scene context quality
            if analysis.scene_confidence > 0.5:
                content_score += 0.2
            
            # Multi-modal consistency
            if analysis.cross_modal_consistency > 0.5:
                content_score += 0.1
            
            quality['content_quality'] = content_score
            
            # Authenticity score (tamper detection, chain validity)
            auth_score = 1.0
            
            if analysis.tamper_detected:
                auth_score -= 0.5
            
            if not analysis.chain_valid:
                auth_score -= 0.3
            
            if not analysis.timestamp_valid:
                auth_score -= 0.2
            
            quality['authenticity_score'] = max(auth_score, 0.0)
            
            # Overall quality score (weighted average)
            quality['quality_score'] = (
                tech_score * 0.4 + 
                content_score * 0.4 + 
                quality['authenticity_score'] * 0.2
            )
            
        except Exception as e:
            logger.warning(f"Quality scoring failed: {e}")
        
        return quality
    
    def _detect_anomalies(self, analysis: 'EvidenceAnalysis') -> Dict:
        """Detect anomalies in evidence using machine learning"""
        anomaly = {
            'is_anomalous': False,
            'anomaly_score': 0.0,
            'anomaly_reasons': []
        }
        
        if self.anomaly_detector is None:
            return anomaly
        
        try:
            # Create feature vector for anomaly detection
            features = [
                analysis.blur_score,
                analysis.brightness,
                len(analysis.detected_objects),
                analysis.people_count,
                analysis.motion_intensity,
                analysis.action_confidence,
                analysis.scene_confidence,
                len(analysis.detected_actions),
                analysis.faces_detected,
                analysis.violence_confidence
            ]
            
            # Normalize features
            features_scaled = self.scaler.fit_transform([features])
            
            # Detect anomaly
            anomaly_prediction = self.anomaly_detector.fit_predict(features_scaled)
            anomaly['anomaly_score'] = float(self.anomaly_detector.decision_function(features_scaled)[0])
            
            if anomaly_prediction[0] == -1:  # Anomaly detected
                anomaly['is_anomalous'] = True
                
                # Determine reasons
                if analysis.blur_score < 50:
                    anomaly['anomaly_reasons'].append('Extremely blurry image')
                
                if analysis.brightness < 0.1 or analysis.brightness > 0.9:
                    anomaly['anomaly_reasons'].append('Unusual lighting conditions')
                
                if len(analysis.detected_objects) == 0 and analysis.has_people:
                    anomaly['anomaly_reasons'].append('People detected but no objects identified')
                
                if analysis.motion_intensity > 0.8:
                    anomaly['anomaly_reasons'].append('Excessive motion detected')
                
                if analysis.violence_confidence > 0.8:
                    anomaly['anomaly_reasons'].append('High violence confidence')
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        
        return anomaly
    
    def _verify_evidence_chain(self, image: Image.Image) -> Dict:
        """Verify evidence chain integrity"""
        chain = {
            'evidence_hash': '',
            'tamper_detected': False,
            'chain_valid': True
        }
        
        try:
            # Calculate evidence hash
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes = img_bytes.getvalue()
            
            chain['evidence_hash'] = hashlib.sha256(img_bytes).hexdigest()
            
            # Check if this hash exists in chain (duplicate detection)
            if chain['evidence_hash'] in self.evidence_chain:
                chain['tamper_detected'] = True
                chain['chain_valid'] = False
                logger.warning(f"Duplicate evidence detected: {chain['evidence_hash']}")
            else:
                # Add to chain
                self.evidence_chain[chain['evidence_hash']] = {
                    'timestamp': datetime.now(timezone.utc),
                    'size': len(img_bytes)
                }
            
        except Exception as e:
            logger.warning(f"Evidence chain verification failed: {e}")
        
        return chain
    
    def _perform_real_time_analysis(self, analysis: 'EvidenceAnalysis') -> Dict:
        """Real-time analysis with progressive validation"""
        realtime = {
            'confidence': 0.0,
            'validation_progression': [],
            'early_false_positive': False
        }
        
        try:
            # Progressive validation stages
            stages = []
            
            # Stage 1: Basic quality check (quick)
            basic_score = 0.0
            if analysis.technical_quality > 0.5:
                basic_score += 0.3
            if analysis.has_people:
                basic_score += 0.4
            if not analysis.is_blurry:
                basic_score += 0.3
            stages.append(basic_score)
            
            # Stage 2: Object detection validation
            object_score = 0.0
            if analysis.detected_objects and 'unknown' not in analysis.detected_objects:
                object_score += 0.5
            if analysis.weapons_detected:
                object_score += 0.3
            if analysis.violence_detected:
                object_score += 0.2
            stages.append(object_score)
            
            # Stage 3: Advanced validation
            advanced_score = 0.0
            if analysis.action_confidence > 0.5:
                advanced_score += 0.3
            if analysis.cross_modal_consistency > 0.5:
                advanced_score += 0.3
            if not analysis.is_anomalous:
                advanced_score += 0.4
            stages.append(advanced_score)
            
            realtime['validation_progression'] = stages
            
            # Calculate real-time confidence (weighted average of stages)
            if stages:
                realtime['confidence'] = sum(stages) / len(stages)
            
            # Early false positive detection
            if len(stages) >= 2 and stages[0] > 0.7 and stages[1] < 0.3:
                realtime['early_false_positive'] = True
                logger.warning("Early false positive detected")
            
        except Exception as e:
            logger.warning(f"Real-time analysis failed: {e}")
        
        return realtime
    
    def _predict_hotspot_probability(self, analysis: 'EvidenceAnalysis', lat: float, lon: float) -> Dict:
        """Predictive hotspot mapping based on evidence analysis"""
        hotspot = {
            'prediction': 0.0,
            'incident_probability': 0.0,
            'resource_score': 0.0
        }
        
        try:
            # Base probability from evidence quality
            base_prob = analysis.confidence_score
            
            # Location-based factors (simplified)
            location_factor = 1.0
            if -1.95 < lat < -1.85 and 30.0 < lon < 30.1:  # Kigali area
                location_factor = 1.2
            elif -2.0 < lat < -1.8 and 29.9 < lon < 30.2:  # Greater Kigali
                location_factor = 1.1
            
            # Time-based factors
            time_factor = 1.0
            current_hour = datetime.now().hour
            if 18 <= current_hour <= 23 or 0 <= current_hour <= 2:  # Night hours
                time_factor = 1.3
            elif 12 <= current_hour <= 14:  # Lunch hours
                time_factor = 1.1
            
            # Evidence-based factors
            evidence_factor = 1.0
            if analysis.violence_detected:
                evidence_factor += 0.2
            if analysis.weapons_detected:
                evidence_factor += 0.3
            if analysis.is_anomalous:
                evidence_factor += 0.1
            
            # Calculate predictions
            hotspot['incident_probability'] = min(base_prob * location_factor * time_factor * evidence_factor, 1.0)
            hotspot['prediction'] = hotspot['incident_probability']
            
            # Resource allocation score
            if hotspot['prediction'] > 0.8:
                hotspot['resource_score'] = 1.0  # High priority
            elif hotspot['prediction'] > 0.6:
                hotspot['resource_score'] = 0.7  # Medium priority
            elif hotspot['prediction'] > 0.4:
                hotspot['resource_score'] = 0.4  # Low priority
            else:
                hotspot['resource_score'] = 0.1  # Minimal priority
            
        except Exception as e:
            logger.warning(f"Hotspot prediction failed: {e}")
        
        return hotspot
    
    def _perform_cross_reference_analysis(self, analysis: 'EvidenceAnalysis', lat: float, lon: float) -> Dict:
        """Cross-reference analysis with existing reports"""
        crossref = {
            'similar_count': 0,
            'cluster_id': None,
            'time_pattern': False,
            'serial_incident': False
        }
        
        try:
            # Simplified cross-reference analysis
            # In production, this would query the database
            
            # Location clustering (simplified)
            cluster_id = f"{lat:.2f}_{lon:.2f}"  # Simple grid-based clustering
            crossref['cluster_id'] = cluster_id
            
            # Simulate similar reports count (would query database)
            # For demo, we'll use heuristics
            if analysis.violence_detected:
                crossref['similar_count'] = 3
            elif analysis.weapons_detected:
                crossref['similar_count'] = 2
            else:
                crossref['similar_count'] = 1
            
            # Time pattern detection
            current_hour = datetime.now().hour
            if 19 <= current_hour <= 23:  # Evening peak
                crossref['time_pattern'] = True
            
            # Serial incident detection
            if crossref['similar_count'] > 2 and analysis.violence_detected:
                crossref['serial_incident'] = True
            
        except Exception as e:
            logger.warning(f"Cross-reference analysis failed: {e}")
        
        return crossref

    # ------------------------------------------------------------------
    # Structured feature extractors (YOLO → ML, LLaVA → ML)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_anomaly_score(raw_score: float, is_anomalous: bool) -> float:
        """
        Convert IsolationForest decision_function output into a 0..1 anomaly risk
        where higher means more suspicious.
        """
        try:
            score = float(raw_score)
        except Exception:
            score = 0.0

        # decision_function is usually positive for normal samples and negative
        # for anomalies, so invert it smoothly around zero.
        risk = 1.0 / (1.0 + np.exp(score * 6.0))
        if is_anomalous:
            risk = max(risk, 0.6)
        else:
            risk = min(risk, 0.45)
        return round(float(max(0.0, min(1.0, risk))), 3)

    # High-risk object set shared across methods
    _HIGH_RISK_OBJECTS = frozenset({
        "panga", "machete", "traditional_knife", "knife", "gun", "pistol",
        "rifle", "weapon", "blood", "injury", "wound", "drugs", "narcotics",
        "cannabis", "heroin", "fire", "explosion",
    })

    # YOLO COCO-class → semantic category mapping
    _YOLO_CATEGORY_SETS = {
        "person":   {"person", "people"},
        "vehicle":  {"car", "truck", "bus", "motorcycle", "bicycle",
                     "motorcycle_taxi", "bicycle_taxi", "motorbike"},
        "weapon":   {"knife", "gun", "panga", "machete", "traditional_knife",
                     "bat", "weapon", "pistol", "rifle"},
        "phone":    {"cell phone", "phone", "tecno_phone", "itel_phone",
                     "samsung_phone", "mobile_money"},
        "money":    {"money", "rwf_note", "cash", "banknote"},
        "bag":      {"backpack", "suitcase", "handbag", "bag", "purse"},
        "document": {"book", "document", "id card", "receipt", "paper"},
        "blood_injury": {"blood", "injury", "wound"},
        "drug_item":    {"drugs", "paraphernalia", "syringe", "cannabis"},
    }

    # LLaVA activity → incident category mapping
    _LLAVA_ACTIVITY_CATEGORIES = {
        "violence":    {"fighting", "hitting", "attacking", "struggling",
                        "assault", "stabbing", "beating", "punching"},
        "theft":       {"running", "grabbing", "taking", "snatching",
                        "pickpocket", "stealing", "fleeing"},
        "suspicious":  {"lurking", "watching", "hiding", "loitering",
                        "following", "spying", "hovering"},
        "domestic":    {"abuse", "threatening", "arguing", "yelling",
                        "shouting", "restraining"},
        "drug":        {"using", "selling", "injecting", "smoking",
                        "distributing", "dealing"},
    }

    def _extract_yolo_ml_features(self, analysis: "EvidenceAnalysis") -> Dict:
        """
        Convert YOLO detected_objects list into structured numerical ML features.
        Returns a dict of feature_name → float (all 0.0–1.0 or counts).
        """
        objects_lower = [o.lower() for o in analysis.detected_objects]
        detected = set(objects_lower)
        object_counts = dict(Counter(objects_lower))

        # Category presence flags
        cats = {}
        for cat_name, cat_set in self._YOLO_CATEGORY_SETS.items():
            cats[cat_name] = bool(detected & cat_set)

        # High-risk objects
        high_risk = [o for o in analysis.detected_objects if o.lower() in self._HIGH_RISK_OBJECTS]
        high_risk_score = min(1.0, len(high_risk) / 3.0)   # capped at 3

        # Object diversity: unique semantic categories / total categories
        active_cats = sum(1 for v in cats.values() if v)
        diversity = active_cats / max(1, len(self._YOLO_CATEGORY_SETS))

        # Total objects (normalised)
        total_norm = min(1.0, len(detected) / 20.0)

        # Expected object match rate vs incident-type rules
        rules = self.enhanced_rules.get(
            getattr(analysis, "_incident_type_id_cache", -1) or -1, {}
        )
        expected_objects = rules.get("expected_objects", [])
        obj_match_rate = 0.5
        if expected_objects:
            hits = sum(1 for o in expected_objects if o.lower() in detected)
            obj_match_rate = hits / len(expected_objects)

        # Composite YOLO feature score (weapons and high-risk objects weighted up)
        yolo_score = (
            float(cats.get("person", False))   * 0.20 +
            float(cats.get("vehicle", False))  * 0.05 +
            float(cats.get("weapon", False))   * 0.30 +
            float(cats.get("phone", False))    * 0.10 +
            float(cats.get("money", False))    * 0.10 +
            high_risk_score                    * 0.15 +
            obj_match_rate                     * 0.10
        )

        # Category-level object counts and presence flags for storage/audit
        object_counts = {}
        for cat_name, cat_set in self._YOLO_CATEGORY_SETS.items():
            object_counts[cat_name] = sum(1 for o in analysis.detected_objects if o.lower() in cat_set)

        return {
            "yolo_person_present":  float(cats.get("person", False)),
            "yolo_vehicle_present": float(cats.get("vehicle", False)),
            "yolo_weapon_present":  float(cats.get("weapon", False)),
            "yolo_phone_present":   float(cats.get("phone", False)),
            "yolo_money_present":   float(cats.get("money", False)),
            "yolo_blood_present":   float(cats.get("blood_injury", False)),
            "yolo_drug_present":    float(cats.get("drug_item", False)),
            "yolo_high_risk_score": round(high_risk_score, 3),
            "yolo_diversity":       round(diversity, 3),
            "yolo_total_norm":      round(total_norm, 3),
            "yolo_obj_match_rate":  round(obj_match_rate, 3),
            "yolo_feature_score":   round(min(1.0, yolo_score), 3),
            "yolo_object_counts":   object_counts,
            "yolo_presence_flags":  {k: bool(v) for k, v in cats.items()},
            "high_risk_objects":    high_risk,
        }

    def _extract_llava_ml_features(self, analysis: "EvidenceAnalysis") -> Dict:
        """
        Convert LLaVA outputs (already stored on analysis) into structured
        numerical ML features.
        Returns a dict of feature_name → float.
        """
        activities_lower = [a.lower() for a in analysis.llava_activities]
        env_lower        = analysis.llava_environment.lower()

        # Activity category scores
        act_scores: Dict[str, float] = {}
        for cat, keywords in self._LLAVA_ACTIVITY_CATEGORIES.items():
            hits = sum(1 for a in activities_lower if any(k in a for k in keywords))
            act_scores[cat] = min(1.0, hits / max(1, len(keywords) * 0.3))

        # Interaction complexity (normalised 0–1 over 5 interactions)
        interaction_complexity = min(1.0, len(analysis.llava_interactions) / 5.0)

        # Incident indicator count (normalised over 5)
        # llava_incident_indicators stored in combined_analysis → count via heuristic
        incident_indicator_count = analysis.llava_incident_indicator_count \
            if hasattr(analysis, "llava_incident_indicator_count") \
            else min(5, analysis.combined_analysis.lower().count("incident indicator"))

        indicator_norm = min(1.0, incident_indicator_count / 5.0)

        # Environment flags
        env_is_public  = float(any(k in env_lower for k in
                                   ("outdoor", "street", "public", "market")))
        env_is_indoor  = float("indoor" in env_lower or "residential" in env_lower)

        # Expected scene match
        rules = self.enhanced_rules.get(
            getattr(analysis, "_incident_type_id_cache", -1) or -1, {}
        )
        expected_scenes = rules.get("expected_scenes", [])
        scene_match = 0.5
        if expected_scenes:
            scene_match = float(
                any(s.lower() in analysis.scene_type.lower() or
                    s.lower() in env_lower for s in expected_scenes)
            )

        # Expected action match
        expected_actions = rules.get("expected_actions", [])
        act_match_rate = 0.5
        if expected_actions and activities_lower:
            hits = sum(1 for a in expected_actions
                       if any(a.lower() in act for act in activities_lower))
            act_match_rate = hits / len(expected_actions)

        # Composite LLaVA feature score
        llava_score = (
            act_scores.get("violence", 0)    * 0.25 +
            act_scores.get("theft", 0)       * 0.20 +
            act_scores.get("suspicious", 0)  * 0.15 +
            act_scores.get("domestic", 0)    * 0.10 +
            act_scores.get("drug", 0)        * 0.10 +
            interaction_complexity           * 0.10 +
            indicator_norm                   * 0.10
        )

        return {
            "llava_violence_activity":    round(act_scores.get("violence", 0), 3),
            "llava_theft_activity":       round(act_scores.get("theft", 0), 3),
            "llava_suspicious_activity":  round(act_scores.get("suspicious", 0), 3),
            "llava_domestic_activity":    round(act_scores.get("domestic", 0), 3),
            "llava_drug_activity":        round(act_scores.get("drug", 0), 3),
            "llava_interaction_complexity": round(interaction_complexity, 3),
            "llava_indicator_norm":       round(indicator_norm, 3),
            "llava_env_is_public":        env_is_public,
            "llava_env_is_indoor":        env_is_indoor,
            "llava_scene_match":          round(scene_match, 3),
            "llava_act_match_rate":       round(act_match_rate, 3),
            "llava_feature_score":        round(min(1.0, llava_score), 3),
            "llava_scene_label":          analysis.llava_scene_label or analysis.scene_type,
            "llava_environment_label":    analysis.llava_environment_label or analysis.llava_environment,
            "llava_activity_scores":      {k: round(v, 3) for k, v in act_scores.items()},
        }

    # ------------------------------------------------------------------
    # Hybrid Decision Engine
    # Phase 0 → Hard rule gates (location + originality)
    # Phase 1 → Text semantic matching (sentence-transformers)
    # Phase 2 → Feature extraction + XGBoost fusion
    # Phase 3 → Label + trust score with gate overrides
    # ------------------------------------------------------------------

    # ── Phase 0a: Location gate ─────────────────────────────────────────────

    def _check_location_gate(self, lat: float, lon: float) -> Dict:
        """
        Deterministic GIS check: is the reported location inside Musanze district?
        Uses shapely polygon containment — no ML involved.
        Returns: {passed, reason, distance_km}
        """
        result = {"passed": True, "reason": "Location within Musanze district", "distance_km": 0.0}
        try:
            if not lat and not lon:
                result["passed"] = True          # no GPS → don't penalise, flag only
                result["reason"] = "No GPS coordinates provided — location unverified"
                return result

            point = Point(lon, lat)              # shapely uses (lon, lat)
            if self.musanze_polygon.contains(point):
                result["passed"] = True
                result["reason"] = "GPS coordinates confirmed within Musanze district"
            else:
                # Compute approximate distance to polygon boundary in km
                nearest = self.musanze_polygon.exterior.interpolate(
                    self.musanze_polygon.exterior.project(point)
                )
                dist_deg = point.distance(nearest)
                dist_km  = dist_deg * 111.0      # ~111 km per degree
                result["passed"] = False
                result["reason"] = (
                    f"Reported location is outside Musanze district "
                    f"(~{dist_km:.1f} km from boundary)"
                )
                result["distance_km"] = round(dist_km, 2)
        except Exception as exc:
            logger.warning(f"Location gate error: {exc}")
            result["passed"] = True              # do not block on gate error
            result["reason"] = f"Location gate error (skipped): {exc}"
        return result

    # ── Phase 0b: Originality gate ──────────────────────────────────────────

    def _check_originality_gate(
        self,
        image_bytes: bytes,
        pil_image: Image.Image,
        report_key: str = "",
    ) -> Dict:
        """
        Deterministic originality checks — run before any ML scoring.
        Checks: perceptual hash duplicate, screenshot/screen-recording detection,
                EXIF consistency.
        Returns: {passed, issues, hash_duplicate, screenshot_detected, exif_consistent}
        """
        gate = {
            "passed": True,
            "issues": [],
            "hash_duplicate": False,
            "screenshot_detected": False,
            "exif_consistent": True,
        }
        try:
            # ── 1. Perceptual hash duplicate detection ───────────────────────
            if _IMAGEHASH_AVAILABLE:
                phash = _imagehash.phash(pil_image)
                threshold = 8                    # hamming distance threshold
                for stored_key, stored_hash in self._phash_store.items():
                    if stored_key != report_key:
                        dist = phash - stored_hash
                        if dist <= threshold:
                            gate["hash_duplicate"] = True
                            gate["issues"].append(
                                f"Perceptual hash duplicate detected "
                                f"(hamming={dist}, matches report {stored_key})"
                            )
                            break
                # Store this image's hash
                if report_key:
                    self._phash_store[report_key] = phash

            # ── 2. Screenshot / screen-recording detection ───────────────────
            img_arr = np.array(pil_image.convert("RGB"))
            h, w = img_arr.shape[:2]

            # Check for common screen aspect ratios (16:9, 18:9, 20:9)
            ratio = w / h if h > 0 else 0
            screen_ratios = [16/9, 18/9, 20/9, 9/16, 9/18]
            is_screen_ratio = any(abs(ratio - r) < 0.05 for r in screen_ratios)

            # Check for uniform horizontal bands at top/bottom (status bar)
            top_band    = img_arr[:max(1, h // 20), :, :]
            bottom_band = img_arr[max(0, h - h // 20):, :, :]
            top_uniform    = top_band.std() < 12
            bottom_uniform = bottom_band.std() < 12

            # Check for very low colour entropy (typical of screenshots of UIs)
            unique_colors = len(np.unique(img_arr.reshape(-1, 3), axis=0))
            low_entropy = unique_colors < 200

            screenshot_signals = sum([is_screen_ratio, top_uniform, bottom_uniform, low_entropy])
            if screenshot_signals >= 3:
                gate["screenshot_detected"] = True
                gate["issues"].append(
                    f"Screenshot/screen-recording suspected "
                    f"(signals: ratio={is_screen_ratio}, top_band={top_uniform}, "
                    f"bottom_band={bottom_uniform}, low_entropy={low_entropy})"
                )

            # ── 3. EXIF / device / capture-time consistency ──────────────────
            exif_issues = []
            try:
                exif = pil_image._getexif() or {}
                tag_names = {TAGS.get(k, k): v for k, v in exif.items()}

                # Must have at least camera make OR model for a real capture
                has_camera_meta = "Make" in tag_names or "Model" in tag_names
                if not has_camera_meta:
                    exif_issues.append("No camera Make/Model in EXIF — may not be original capture")

                # Timestamp sanity (not in future, not older than 10 years)
                dt_str = tag_names.get("DateTimeOriginal") or tag_names.get("DateTime")
                if dt_str:
                    try:
                        exif_dt = datetime.strptime(str(dt_str), "%Y:%m:%d %H:%M:%S")
                        now = datetime.now()
                        age_days = (now - exif_dt).days
                        if exif_dt > now:
                            exif_issues.append("EXIF timestamp is in the future")
                        elif age_days > 3650:
                            exif_issues.append(f"EXIF timestamp is {age_days} days old (>10 years)")
                    except ValueError:
                        exif_issues.append("EXIF timestamp unparseable")
                else:
                    exif_issues.append("No capture timestamp in EXIF")

                # Software field suggests edited image
                software = str(tag_names.get("Software", "")).lower()
                editing_keywords = ["photoshop", "lightroom", "gimp", "snapseed", "facetune"]
                for kw in editing_keywords:
                    if kw in software:
                        exif_issues.append(f"Editing software detected in EXIF: {software}")
                        break

            except Exception:
                exif_issues.append("EXIF data unreadable")

            if exif_issues:
                gate["exif_consistent"] = False
                gate["issues"].extend(exif_issues)

            # ── Gate decision ────────────────────────────────────────────────
            # Hard failures: hash duplicate or screenshot → force UNDER_REVIEW
            if gate["hash_duplicate"] or gate["screenshot_detected"]:
                gate["passed"] = False
            # Soft failures: EXIF issues alone → flag but don't block gate
            # (they will lower the trust score through authenticity_score)

        except Exception as exc:
            logger.warning(f"Originality gate error: {exc}")

        return gate

    # ── Phase 1: Text semantic matching ─────────────────────────────────────

    def _embed(self, text: str) -> Optional[Any]:
        """Return a normalised embedding vector, or None on failure."""
        if not self.text_model or not text:
            return None
        try:
            return self.text_model.encode(
                text, normalize_embeddings=True, convert_to_tensor=False
            )
        except Exception as exc:
            logger.warning(f"Embedding failed: {exc}")
            return None

    @staticmethod
    def _cosine_sim(a: Any, b: Any) -> float:
        """Cosine similarity for two L2-normalised vectors; maps to [0, 1]."""
        try:
            raw = float(np.dot(a, b))          # already in [-1, 1] for unit vectors
            return round(max(0.0, min(1.0, (raw + 1.0) / 2.0)), 3)
        except Exception:
            return 0.5

    def _compute_text_features(
        self,
        incident_type_id: Optional[int],
        description: str,
    ) -> Dict:
        """
        Kept as thin wrapper → delegates to _compute_semantic_match.
        Preserves backwards-compatible keys.
        """
        result = self._compute_semantic_match(incident_type_id, description, "")
        return {
            "similarity":        result["desc_vs_type"],
            "mismatch_score":    round(1.0 - result["desc_vs_type"], 3),
            "mismatch_detected": result["desc_vs_type"] < 0.35,
            **result,   # also expose full semantic fields
        }

    def _compute_semantic_match(
        self,
        incident_type_id: Optional[int],
        description: str,
        llava_scene_description: str,
    ) -> Dict:
        """
        Tri-way embedding-based semantic similarity:
          • desc ↔ incident-type anchor  (how well user description matches incident type)
          • desc ↔ LLaVA scene           (how well user description matches visual reality)
          • LLaVA scene ↔ incident anchor (how well the scene itself fits the incident type)

        Combined semantic_match_score = weighted average of all three.
        """
        result = {
            "desc_vs_type":       0.5,
            "desc_vs_llava":      0.5,
            "llava_vs_type":      0.5,
            "semantic_match_score": 0.5,
            "mismatch_detected":  False,
        }
        if not self.text_model:
            return result

        try:
            anchor_text = self._incident_anchors.get(incident_type_id or -1, "")

            # Anchor embedding (cached)
            if incident_type_id and anchor_text:
                if incident_type_id not in self._anchor_embeddings:
                    self._anchor_embeddings[incident_type_id] = self._embed(anchor_text)
                anchor_emb = self._anchor_embeddings.get(incident_type_id)
            else:
                anchor_emb = None

            desc_emb  = self._embed(description)           if description else None
            llava_emb = self._embed(llava_scene_description) if llava_scene_description else None

            # Pairwise similarities
            if desc_emb is not None and anchor_emb is not None:
                result["desc_vs_type"] = self._cosine_sim(desc_emb, anchor_emb)

            if desc_emb is not None and llava_emb is not None:
                result["desc_vs_llava"] = self._cosine_sim(desc_emb, llava_emb)

            if llava_emb is not None and anchor_emb is not None:
                result["llava_vs_type"] = self._cosine_sim(llava_emb, anchor_emb)

            # Combined score (desc_vs_type weighted most — it's user intent)
            result["semantic_match_score"] = round(
                result["desc_vs_type"]  * 0.50 +
                result["desc_vs_llava"] * 0.30 +
                result["llava_vs_type"] * 0.20,
                3,
            )
            result["mismatch_detected"] = result["desc_vs_type"] < 0.35

        except Exception as exc:
            logger.warning(f"Semantic match failed: {exc}")

        return result

    def _compute_rule_based_score(
        self,
        incident_type_id: Optional[int],
        description: str,
        analysis: "EvidenceAnalysis",
    ) -> float:
        """
        Scalar rule-based validation score mirrored from the production
        validation logic so the final decision engine always sees a direct rule
        signal before assigning a verdict.
        """
        rules = self.enhanced_rules.get(incident_type_id or -1, {})
        if not rules:
            return 0.0

        score = 0.0
        max_score = 0.0
        detected_objects = {obj.lower() for obj in analysis.detected_objects}
        detected_actions = {act.lower() for act in analysis.detected_actions}
        description_lower = (description or "").lower()

        expected_objects = [obj.lower() for obj in rules.get("expected_objects", [])]
        if expected_objects:
            max_score += 0.15
            object_matches = sum(1 for obj in expected_objects if obj in detected_objects)
            if object_matches:
                score += 0.15 * (object_matches / len(expected_objects))

        max_score += 0.10
        if analysis.has_people:
            score += 0.10

        expected_actions = [act.lower() for act in rules.get("expected_actions", [])]
        max_score += 0.15
        if expected_actions and detected_actions:
            action_matches = sum(1 for action in expected_actions if action in detected_actions)
            if action_matches:
                score += 0.15 * (action_matches / len(expected_actions))

        expected_scenes = [scene.lower() for scene in rules.get("expected_scenes", [])]
        max_score += 0.10
        if expected_scenes:
            scene_match = any(
                scene in analysis.scene_type.lower() or
                scene in analysis.llava_environment.lower() or
                (scene == "market" and scene in description_lower)
                for scene in expected_scenes
            )
            if scene_match or analysis.scene_confidence > 0.7:
                score += 0.10

        max_score += 0.10
        if analysis.technical_quality > 0.7:
            score += 0.10
        elif analysis.technical_quality > 0.5:
            score += 0.05

        max_score += 0.10
        if analysis.content_quality > 0.7:
            score += 0.10
        elif analysis.content_quality > 0.5:
            score += 0.05

        max_score += 0.10
        if analysis.authenticity_score > 0.8:
            score += 0.10
        elif analysis.authenticity_score > 0.6:
            score += 0.05

        max_score += 0.05
        if incident_type_id in [2, 5]:
            if analysis.violence_detected:
                score += 0.05
        else:
            score += 0.05

        max_score += 0.05
        if analysis.cross_modal_consistency > 0.7:
            score += 0.05
        elif analysis.cross_modal_consistency > 0.5:
            score += 0.025

        max_score += 0.05
        if not analysis.is_anomalous:
            score += 0.05

        max_score += 0.05
        if analysis.faces_detected > 0:
            if analysis.privacy_blurred:
                score += 0.05
        else:
            score += 0.05

        keywords = [keyword.lower() for keyword in rules.get("keywords", [])]
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword in description_lower)
            if keyword_matches:
                bonus = 0.10 * (keyword_matches / len(keywords))
                score += bonus
                max_score += bonus

        if max_score <= 0:
            return 0.0
        return round(max(0.0, min(1.0, score / max_score)), 3)

    def _get_incident_rules(self, incident_type_id: Optional[int]) -> Dict[str, Any]:
        return self.enhanced_rules.get(incident_type_id or -1, {}) or {}

    def _get_incident_name(self, incident_type_id: Optional[int]) -> str:
        rules = self._get_incident_rules(incident_type_id)
        return str(rules.get("incident_name") or f"incident_{incident_type_id or 'unknown'}")

    def _compute_evidence_match_score(
        self,
        incident_type_id: Optional[int],
        text_features: Dict[str, Any],
        analysis: "EvidenceAnalysis",
    ) -> Dict[str, Any]:
        rules = self._get_incident_rules(incident_type_id)
        expected_objects = [obj.lower() for obj in rules.get("expected_objects", [])]
        detected_objects = {obj.lower() for obj in (analysis.detected_objects or [])}
        object_match_ratio = 0.0
        if expected_objects:
            object_match_ratio = sum(1 for obj in expected_objects if obj in detected_objects) / len(expected_objects)

        scene_match = 0.0
        llava_features = self._extract_llava_ml_features(analysis)
        try:
            scene_match = float(llava_features.get("llava_scene_match", 0.0) or 0.0)
        except Exception:
            scene_match = 0.0

        semantic_similarity = float(text_features.get("desc_vs_llava", 0.5) or 0.5)
        caption_incident_fit = float(text_features.get("llava_vs_type", 0.5) or 0.5)
        yolo_support = float(max(analysis.yolo_obj_match_rate, object_match_ratio, analysis.yolo_feature_score))
        llava_support = float(max(scene_match, analysis.llava_feature_score))
        model_consistency = float(analysis.yolo_llava_consistency or 0.0)

        evidence_match_score = (
            semantic_similarity * 0.30 +
            yolo_support * 0.25 +
            llava_support * 0.20 +
            caption_incident_fit * 0.15 +
            model_consistency * 0.10
        )

        if semantic_similarity < 0.30:
            evidence_match_score *= 0.55

        contradiction = False
        contradiction_reasons: List[str] = []
        if text_features.get("mismatch_detected") and semantic_similarity < 0.30:
            contradiction = True
            contradiction_reasons.append("description_conflicts_with_caption")
        if expected_objects and yolo_support <= 0.0 and llava_support < 0.30:
            contradiction = True
            contradiction_reasons.append("required_objects_missing")
        if model_consistency < 0.20 and semantic_similarity < 0.30:
            contradiction = True
            contradiction_reasons.append("yolo_llava_and_text_disagree")

        if contradiction:
            evidence_match_score = 0.0

        reasoning_bits = [
            f"YOLO support={yolo_support:.2f}",
            f"LLaVA support={llava_support:.2f}",
            f"text-caption similarity={semantic_similarity:.2f}",
            f"scene fit={caption_incident_fit:.2f}",
        ]
        if contradiction_reasons:
            reasoning_bits.append("contradictions=" + ",".join(contradiction_reasons))

        return {
            "evidence_match_score": round(max(0.0, min(1.0, evidence_match_score)), 3),
            "similarity_score": round(max(0.0, min(1.0, semantic_similarity)), 3),
            "contradiction": contradiction,
            "reasoning": "; ".join(reasoning_bits),
            "required_objects_present": object_match_ratio > 0.0 if expected_objects else bool(detected_objects),
            "high_confidence_evidence_present": bool(detected_objects or analysis.llava_scene_description),
            "object_match_ratio": round(object_match_ratio, 3),
        }

    def _compute_rule_gate(
        self,
        incident_type_id: Optional[int],
        analysis: "EvidenceAnalysis",
        evidence_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        rules = self._get_incident_rules(incident_type_id)
        expected_objects = [obj.lower() for obj in rules.get("expected_objects", [])]
        failures: List[str] = []

        if not evidence_result.get("high_confidence_evidence_present"):
            failures.append("no_evidence_present")

        if evidence_result.get("contradiction"):
            failures.append("evidence_contradiction_detected")

        if expected_objects and not evidence_result.get("required_objects_present"):
            failures.append("required_objects_missing")

        # The current pipeline already discards YOLO detections below 0.5 confidence.
        # If nothing survived detection and visual-language support is also weak,
        # treat that as failing the confidence gate.
        weak_detector_signal = (
            not analysis.detected_objects and
            analysis.yolo_feature_score < 0.40 and
            analysis.llava_feature_score < 0.30
        )
        if weak_detector_signal:
            failures.append("weak_detection_confidence")

        passed = not failures
        return {
            "rule_score": 1 if passed else 0,
            "passed": passed,
            "failures": failures,
        }

    # ── Phase 2: Feature vector + XGBoost fusion ────────────────────────────

    def _extract_fusion_features(
        self,
        analysis: "EvidenceAnalysis",
        text_features: Dict,
        historical_trust: float = 0.5,
        community_votes: float = 0.5,
    ) -> Tuple[List[float], List[str]]:
        """
        Build the enriched multimodal feature vector consumed by the final
        fusion layer. The order is stable so a future XGBoost model can be
        retrained against the same schema.
        """
        yolo_features = self._extract_yolo_ml_features(analysis)
        llava_features = self._extract_llava_ml_features(analysis)

        analysis.yolo_feature_score = yolo_features.get("yolo_feature_score", 0.0)
        analysis.yolo_person_present = bool(yolo_features.get("yolo_person_present", 0.0))
        analysis.yolo_vehicle_present = bool(yolo_features.get("yolo_vehicle_present", 0.0))
        analysis.yolo_weapon_present = bool(yolo_features.get("yolo_weapon_present", 0.0))
        analysis.yolo_high_risk_objects = yolo_features.get("high_risk_objects", [])
        analysis.yolo_object_diversity = yolo_features.get("yolo_diversity", 0.0)
        analysis.yolo_obj_match_rate = yolo_features.get("yolo_obj_match_rate", 0.0)
        analysis.yolo_object_counts = yolo_features.get("yolo_object_counts", {})
        analysis.yolo_presence_flags = yolo_features.get("yolo_presence_flags", {})

        analysis.llava_feature_score = llava_features.get("llava_feature_score", 0.0)
        analysis.llava_violence_activity_score = llava_features.get("llava_violence_activity", 0.0)
        analysis.llava_theft_activity_score = llava_features.get("llava_theft_activity", 0.0)
        analysis.llava_suspicious_activity_score = llava_features.get("llava_suspicious_activity", 0.0)
        analysis.llava_interaction_complexity = llava_features.get("llava_interaction_complexity", 0.0)
        analysis.llava_activity_scores = llava_features.get("llava_activity_scores", {})
        analysis.llava_scene_label = llava_features.get("llava_scene_label", analysis.llava_scene_label)
        analysis.llava_environment_label = llava_features.get("llava_environment_label", analysis.llava_environment_label)

        features = [
            text_features.get("semantic_match_score", 0.5),
            text_features.get("desc_vs_type", text_features.get("similarity", 0.5)),
            text_features.get("desc_vs_llava", 0.5),
            text_features.get("llava_vs_type", 0.5),
            text_features.get("mismatch_score", 0.5),
            analysis.rule_based_score,
            analysis.evidence_quality_score,
            analysis.anomaly_risk_score,
            yolo_features.get("yolo_feature_score", 0.0),
            yolo_features.get("yolo_person_present", 0.0),
            yolo_features.get("yolo_vehicle_present", 0.0),
            yolo_features.get("yolo_weapon_present", 0.0),
            yolo_features.get("yolo_high_risk_score", 0.0),
            yolo_features.get("yolo_diversity", 0.0),
            yolo_features.get("yolo_total_norm", 0.0),
            yolo_features.get("yolo_obj_match_rate", 0.0),
            llava_features.get("llava_feature_score", 0.0),
            llava_features.get("llava_violence_activity", 0.0),
            llava_features.get("llava_theft_activity", 0.0),
            llava_features.get("llava_suspicious_activity", 0.0),
            llava_features.get("llava_interaction_complexity", 0.0),
            llava_features.get("llava_indicator_norm", 0.0),
            llava_features.get("llava_env_is_public", 0.0),
            llava_features.get("llava_env_is_indoor", 0.0),
            llava_features.get("llava_scene_match", 0.0),
            llava_features.get("llava_act_match_rate", 0.0),
            analysis.yolo_llava_consistency,
            analysis.quality_score,
            analysis.technical_quality,
            analysis.content_quality,
            analysis.authenticity_score,
            float(analysis.tamper_detected),
            float(analysis.hash_duplicate_detected),
            float(analysis.screenshot_detected),
            float(not analysis.exif_consistent),
            float(not analysis.chain_valid),
            analysis.violence_confidence,
            float(bool(analysis.weapons_detected)),
            float(not analysis.location_gate_passed),
            historical_trust,
            community_votes,
        ]

        names = [
            "semantic_match_score",
            "desc_vs_type",
            "desc_vs_llava",
            "llava_vs_type",
            "text_mismatch",
            "rule_based_score",
            "evidence_quality_score",
            "anomaly_risk_score",
            "yolo_feature_score",
            "yolo_person_present",
            "yolo_vehicle_present",
            "yolo_weapon_present",
            "yolo_high_risk_score",
            "yolo_diversity",
            "yolo_total_norm",
            "yolo_obj_match_rate",
            "llava_feature_score",
            "llava_violence_activity",
            "llava_theft_activity",
            "llava_suspicious_activity",
            "llava_interaction_complexity",
            "llava_indicator_norm",
            "llava_env_is_public",
            "llava_env_is_indoor",
            "llava_scene_match",
            "llava_act_match_rate",
            "model_consistency",
            "overall_quality",
            "technical_quality",
            "content_quality",
            "authenticity",
            "tamper",
            "hash_duplicate",
            "screenshot",
            "exif_bad",
            "chain_broken",
            "violence_conf",
            "weapons_present",
            "location_failed",
            "reporter_trust",
            "community_votes",
        ]

        normalized = []
        for value in features:
            try:
                normalized.append(max(0.0, min(1.0, float(value))))
            except Exception:
                normalized.append(0.0)
        return normalized, names

    def _xgb_fallback_score(self, features: List[float], feature_names: List[str]) -> Dict:
        """
        Rule-weighted enriched fallback used when an updated XGBoost decision
        model is unavailable. The weights intentionally force every required
        signal group into the final score.
        """
        f = dict(zip(feature_names, features))

        semantic_score = (
            f["semantic_match_score"] * 0.18 +
            f["desc_vs_llava"] * 0.07 +
            f["llava_vs_type"] * 0.05
        )
        rule_score = f["rule_based_score"] * 0.20
        yolo_score = (
            f["yolo_feature_score"] * 0.10 +
            f["yolo_obj_match_rate"] * 0.05 +
            f["yolo_high_risk_score"] * 0.03 +
            f["yolo_person_present"] * 0.02
        )
        llava_score = (
            f["llava_feature_score"] * 0.10 +
            f["llava_scene_match"] * 0.05 +
            f["llava_act_match_rate"] * 0.03 +
            f["llava_interaction_complexity"] * 0.02
        )
        quality_score = f["evidence_quality_score"] * 0.10
        consistency_score = f["model_consistency"] * 0.05
        context_score = (
            f["reporter_trust"] * 0.03 +
            f["community_votes"] * 0.02
        )

        raw = (
            semantic_score +
            rule_score +
            yolo_score +
            llava_score +
            quality_score +
            consistency_score +
            context_score
        )

        penalties = (
            f["anomaly_risk_score"] * 0.14 +
            f["tamper"] * 0.16 +
            f["hash_duplicate"] * 0.18 +
            f["screenshot"] * 0.15 +
            f["exif_bad"] * 0.06 +
            f["chain_broken"] * 0.08 +
            f["location_failed"] * 0.12 +
            f["text_mismatch"] * 0.05
        )

        trust = max(0.0, min(1.0, raw - penalties))

        if trust >= 0.70:
            label = "REAL"
            proba = {
                "REAL": round(trust, 3),
                "SUSPICIOUS": round(max(0.0, 1.0 - trust), 3),
                "REJECTED": 0.0,
            }
        elif trust >= 0.40:
            label = "SUSPICIOUS"
            proba = {
                "REAL": round(max(0.0, trust - 0.15), 3),
                "SUSPICIOUS": round(trust, 3),
                "REJECTED": round(max(0.0, 1.0 - trust), 3),
            }
        else:
            label = "REJECTED"
            proba = {
                "REAL": 0.0,
                "SUSPICIOUS": round(max(0.0, trust), 3),
                "REJECTED": round(max(0.6, 1.0 - trust), 3),
            }

        return {
            "label": label, "trust_score": round(trust, 3),
            "proba": proba,
            "breakdown": {
                "semantic_match_score": round(f["semantic_match_score"], 3),
                "rule_based_score": round(f["rule_based_score"], 3),
                "yolo_feature_score": round(f["yolo_feature_score"], 3),
                "llava_feature_score": round(f["llava_feature_score"], 3),
                "evidence_quality_score": round(f["evidence_quality_score"], 3),
                "anomaly_score": round(f["anomaly_risk_score"], 3),
                "semantic_component": round(semantic_score, 3),
                "rule_component": round(rule_score, 3),
                "yolo_component": round(yolo_score, 3),
                "llava_component": round(llava_score, 3),
                "quality_component": round(quality_score, 3),
                "consistency_component": round(consistency_score, 3),
                "context_component": round(context_score, 3),
                "penalties": round(penalties, 3),
                "raw": round(raw, 3),
            },
        }

    # ── Phase 3: Main decision engine entry point ────────────────────────────

    def _run_decision_engine(
        self,
        analysis: "EvidenceAnalysis",
        incident_type_id: Optional[int] = None,
        description: str = "",
        reported_lat: float = 0.0,
        reported_lon: float = 0.0,
        historical_trust: float = 0.5,
        community_votes: float = 0.5,
        report_key: str = "",
        image_bytes: Optional[bytes] = None,
        pil_image: Optional[Image.Image] = None,
    ) -> Dict:
        """
        Hybrid multimodal decision engine.

        PHASE 0 — Hard rule gates (deterministic — block before ML):
          • Location gate  : Musanze polygon containment (GIS)
          • Originality gate: pHash duplicate, screenshot, EXIF consistency

        PHASE 1 — Text semantic matching (sentence-transformers):
          • Cosine similarity between description and incident-type anchor

        PHASE 2 — XGBoost fusion (20 features):
          • 40% rule match (text + YOLO objects + actions)
          • 30% YOLO–LLaVA consistency
          • 20% evidence quality / authenticity
          • 10% scene context / location / reporter history

        PHASE 3 — Label assignment with gate overrides:
          • Location outside Musanze      → REJECTED (hard)
          • Duplicate / screenshot        → UNDER_REVIEW (hard)
          • trust_score ≥ 0.65           → REAL
          • trust_score ≥ 0.35           → SUSPICIOUS
          • trust_score < 0.35           → REJECTED
        """
        result = {
            "decision": "REJECTED",
            "label": "REJECTED",
            "trust_score": 0.0,
            "xgboost_score": 0.0,
            "proba": {},
            "reasoning": "",
            "breakdown": {},
            "gate_location": {},
            "gate_originality": {},
            "text_features": {},
            "semantic_match_score": 0.0,
            "rule_based_score": 0.0,
            "consistency_score": 0.0,
            "similarity_score": 0.0,
            "evidence_match_score": 0.0,
            "contradiction": False,
            "ai_score": 0.0,
            "rule_score": 0.0,
            "final_score": 0.0,
            "yolo_feature_score": 0.0,
            "llava_feature_score": 0.0,
            "anomaly_score": 0.0,
            "evidence_quality_score": 0.0,
            "feature_summary": {},
            "details": {},
            "final_verdict_reason": "",
        }
        try:
            reasoning_parts: list[str] = []

            # ══════════════════════════════════════════════════════════════
            # PHASE 0 — Hard rule gates (deterministic)
            # ══════════════════════════════════════════════════════════════

            # 0a. Location gate
            loc_gate = self._check_location_gate(reported_lat, reported_lon)
            result["gate_location"] = loc_gate
            analysis.location_gate_passed = loc_gate["passed"]
            analysis.location_gate_reason = loc_gate["reason"]
            reasoning_parts.append(f"[Location] {loc_gate['reason']}")

            # 0b. Originality gate
            orig_gate = {"passed": True, "issues": [], "hash_duplicate": False,
                         "screenshot_detected": False, "exif_consistent": True}
            if image_bytes and pil_image:
                orig_gate = self._check_originality_gate(image_bytes, pil_image, report_key)
            result["gate_originality"] = orig_gate
            analysis.originality_gate_passed = orig_gate["passed"]
            analysis.originality_gate_issues  = orig_gate["issues"]
            analysis.hash_duplicate_detected  = orig_gate["hash_duplicate"]
            analysis.screenshot_detected      = orig_gate["screenshot_detected"]
            analysis.exif_consistent          = orig_gate["exif_consistent"]
            if orig_gate["issues"]:
                reasoning_parts.append("[Originality] " + "; ".join(orig_gate["issues"]))

            # ══════════════════════════════════════════════════════════════
            # PHASE 1 — Text semantic matching
            # ══════════════════════════════════════════════════════════════
            text_features = self._compute_semantic_match(
                incident_type_id,
                description,
                analysis.llava_scene_description,
            )
            text_features["similarity"] = text_features.get("desc_vs_type", 0.5)
            text_features["mismatch_score"] = round(
                1.0 - text_features.get("desc_vs_type", 0.5),
                3,
            )
            result["text_features"] = text_features
            analysis.text_similarity_score = text_features["similarity"]
            analysis.incident_type_mismatch = text_features["mismatch_detected"]
            analysis.semantic_match_score = text_features.get("semantic_match_score", 0.5)
            analysis.desc_vs_llava_similarity = text_features.get("desc_vs_llava", 0.5)
            analysis.llava_vs_type_similarity = text_features.get("llava_vs_type", 0.5)
            consistency_score = float(text_features.get("desc_vs_type", 0.5) or 0.5)
            result["consistency_score"] = round(consistency_score, 3)
            reasoning_parts.append(
                f"[Semantic] consistency={consistency_score:.2f}"
                + (" ⚠ TYPE MISMATCH" if text_features["mismatch_detected"] else "")
            )

            # ══════════════════════════════════════════════════════════════
            # PHASE 2 — XGBoost fusion
            # ══════════════════════════════════════════════════════════════

            # Cache incident_type_id so _extract_fusion_features can read it
            analysis._incident_type_id_cache = incident_type_id  # type: ignore[attr-defined]
            analysis.rule_based_score = self._compute_rule_based_score(
                incident_type_id,
                description,
                analysis,
            )
            result["semantic_match_score"] = analysis.semantic_match_score
            result["rule_based_score"] = analysis.rule_based_score

            evidence_result = self._compute_evidence_match_score(
                incident_type_id,
                text_features,
                analysis,
            )
            result["similarity_score"] = evidence_result["similarity_score"]
            result["evidence_match_score"] = evidence_result["evidence_match_score"]
            result["contradiction"] = evidence_result["contradiction"]
            reasoning_parts.append(
                f"[Evidence] match={evidence_result['evidence_match_score']:.2f}; "
                f"similarity={evidence_result['similarity_score']:.2f}"
                + (" ⚠ CONTRADICTION" if evidence_result["contradiction"] else "")
            )

            rule_gate = self._compute_rule_gate(
                incident_type_id,
                analysis,
                evidence_result,
            )
            ai_score = ((consistency_score * 0.5) + (evidence_result["evidence_match_score"] * 0.5)) * 60.0
            if evidence_result["similarity_score"] < 0.30:
                ai_score *= 0.60
            rule_score_final = float(rule_gate["rule_score"] * 40)
            final_score = max(0.0, min(100.0, ai_score + rule_score_final))

            result["ai_score"] = round(ai_score, 3)
            result["rule_score"] = round(rule_score_final, 3)
            result["final_score"] = round(final_score, 3)

            features, feature_names = self._extract_fusion_features(
                analysis, text_features, historical_trust, community_votes
            )

            expected_feature_count = getattr(self.xgb_model, "n_features_in_", None) if self.xgb_model is not None else None
            can_use_xgb = bool(
                self.xgb_model is not None and
                _XGB_AVAILABLE and
                expected_feature_count == len(features)
            )
            if self.xgb_model is not None and _XGB_AVAILABLE and not can_use_xgb:
                logger.warning(
                    "Decision XGBoost model skipped because it expects %s features but the enriched pipeline produced %s",
                    expected_feature_count,
                    len(features),
                )

            if can_use_xgb:
                import numpy as _np
                feat_arr = _np.array([features])
                proba_arr = self.xgb_model.predict_proba(feat_arr)[0]
                pred_idx  = int(proba_arr.argmax())
                label     = self.xgb_label_map.get(pred_idx, "SUSPICIOUS")
                trust_score = float(proba_arr[pred_idx])
                proba = {
                    "REAL":       round(float(proba_arr[0]), 3),
                    "SUSPICIOUS": round(float(proba_arr[1]), 3),
                    "REJECTED":   round(float(proba_arr[2]), 3),
                }
                xgb_result = {
                    "label": label, "trust_score": round(trust_score, 3),
                    "proba": proba, "breakdown": dict(zip(feature_names, features)),
                }
                reasoning_parts.append(
                    f"[XGBoost] label={label} trust={trust_score:.2f} "
                    f"(REAL={proba['REAL']:.2f} SUSP={proba['SUSPICIOUS']:.2f} REJ={proba['REJECTED']:.2f})"
                )
            else:
                xgb_result = self._xgb_fallback_score(features, feature_names)
                reasoning_parts.append(
                    f"[Fallback Fusion] label={xgb_result['label']} trust={xgb_result['trust_score']:.2f}"
                )

            xgb_result.setdefault("breakdown", {})
            xgb_result["breakdown"].update({
                "semantic_match_score": round(analysis.semantic_match_score, 3),
                "rule_based_score": round(analysis.rule_based_score, 3),
                "consistency_score": round(consistency_score, 3),
                "similarity_score": round(evidence_result["similarity_score"], 3),
                "evidence_match_score": round(evidence_result["evidence_match_score"], 3),
                "contradiction": bool(evidence_result["contradiction"]),
                "rule_gate_score": rule_gate["rule_score"],
                "ai_score": round(ai_score, 3),
                "rule_score_final": round(rule_score_final, 3),
                "final_score": round(final_score, 3),
                "yolo_feature_score": round(analysis.yolo_feature_score, 3),
                "llava_feature_score": round(analysis.llava_feature_score, 3),
                "anomaly_score": round(analysis.anomaly_risk_score, 3),
                "evidence_quality_score": round(analysis.evidence_quality_score, 3),
            })

            # ══════════════════════════════════════════════════════════════
            # PHASE 3 — Gate overrides → final label
            # ══════════════════════════════════════════════════════════════

            legacy_label = xgb_result["label"]
            trust_score = xgb_result["trust_score"]
            workflow_decision = "REJECTED"
            hard_reject_reason = ""

            # Hard gate overrides (deterministic — not negotiable)
            if not loc_gate["passed"]:
                legacy_label = "REJECTED"
                trust_score = 0.0
                workflow_decision = "REJECTED"
                hard_reject_reason = "location outside Musanze district"
                reasoning_parts.append(
                    "HARD REJECT: location outside Musanze district — report invalid"
                )
            elif (
                evidence_result["evidence_match_score"] <= 0.0 or
                evidence_result["contradiction"] or
                rule_gate["rule_score"] == 0
            ):
                legacy_label = "REJECTED"
                workflow_decision = "REJECTED"
                trust_score = min(trust_score, final_score / 100.0)
                if evidence_result["contradiction"]:
                    hard_reject_reason = "evidence contradicts the description"
                elif rule_gate["rule_score"] == 0:
                    hard_reject_reason = "rule-based validation failed"
                else:
                    hard_reject_reason = "evidence match score is zero"
                reasoning_parts.append(f"HARD REJECT: {hard_reject_reason}")
            elif not orig_gate["passed"]:
                legacy_label = "SUSPICIOUS"
                workflow_decision = "REVIEW"
                trust_score = min(trust_score, 0.40)
                reasoning_parts.append(
                    "HARD FLAG: duplicate/screenshot evidence — downgraded to SUSPICIOUS"
                )
            elif analysis.tamper_detected:
                legacy_label = "SUSPICIOUS" if legacy_label == "REAL" else legacy_label
                trust_score = min(trust_score, 0.60)
                workflow_decision = "REVIEW"
                reasoning_parts.append(
                    "TAMPER CAP: tamper detected — REAL verdict blocked"
                )
            else:
                if final_score >= 70:
                    workflow_decision = "ACCEPTED"
                    legacy_label = "REAL"
                elif final_score >= 50:
                    workflow_decision = "REVIEW"
                    legacy_label = "SUSPICIOUS"
                else:
                    workflow_decision = "REJECTED"
                    legacy_label = "REJECTED"

            if hard_reject_reason:
                final_reason = f"REJECTED because {hard_reject_reason}."
            elif workflow_decision == "ACCEPTED":
                final_reason = (
                    f"ACCEPTED because the incident type and description are consistent "
                    f"({consistency_score:.2f}) and the evidence strongly matches ({evidence_result['evidence_match_score']:.2f})."
                )
            elif workflow_decision == "REVIEW":
                final_reason = (
                    f"REVIEW because the evidence partially matches the incident "
                    f"(score {evidence_result['evidence_match_score']:.2f}) but is not strong enough for acceptance."
                )
            else:
                final_reason = (
                    f"REJECTED because the multimodal signals did not meet the strict validation threshold "
                    f"(final score {final_score:.1f})."
                )

            result["decision"] = workflow_decision
            result["label"] = legacy_label
            result["trust_score"] = round(trust_score, 3)
            result["xgboost_score"] = round(xgb_result.get("trust_score", 0.0), 3)
            result["proba"] = xgb_result.get("proba", {})
            result["yolo_feature_score"] = round(analysis.yolo_feature_score, 3)
            result["llava_feature_score"] = round(analysis.llava_feature_score, 3)
            result["anomaly_score"] = round(analysis.anomaly_risk_score, 3)
            result["evidence_quality_score"] = round(analysis.evidence_quality_score, 3)
            result["breakdown"]   = xgb_result.get("breakdown", {})
            result["feature_summary"] = {
                "yolo_objects": analysis.detected_objects,
                "yolo_object_counts": analysis.yolo_object_counts,
                "yolo_presence_flags": analysis.yolo_presence_flags,
                "llava_scene": analysis.llava_scene_label or analysis.llava_scene_description,
                "llava_actions": analysis.llava_activities,
                "llava_activity_scores": analysis.llava_activity_scores,
                "high_risk_objects": analysis.yolo_high_risk_objects,
                "environment_label": analysis.llava_environment_label or analysis.llava_environment,
                "interaction_complexity_score": round(analysis.llava_interaction_complexity, 3),
            }
            result["details"] = {
                "consistency_score": round(consistency_score, 3),
                "similarity_score": round(evidence_result["similarity_score"], 3),
                "evidence_match_score": round(evidence_result["evidence_match_score"], 3),
                "contradiction": bool(evidence_result["contradiction"]),
            }
            result["breakdown"]["workflow_decision"] = workflow_decision
            result["final_verdict_reason"] = final_reason
            result["reasoning"]   = " | ".join(reasoning_parts)

            analysis.xgboost_score = result["xgboost_score"]
            analysis.xgboost_probabilities = result["proba"]
            analysis.final_verdict_reason = result["final_verdict_reason"]

        except Exception as exc:
            logger.warning(f"Decision engine failed: {exc}")
            result["reasoning"] = f"Decision engine error: {exc}"

        return result

    def _run_llava_analysis(self, image_bytes: bytes, incident_type_id: Optional[int] = None) -> Dict:
        """
        Send the image to LLaVA (via Ollama) with a structured JSON prompt.
        Returns a dict with keys: scene_description, environment, activities,
        objects, interactions, incident_indicators, consistency_notes.
        Falls back to empty defaults on any error so the pipeline continues.
        """
        import base64

        default = {
            "scene_description": "",
            "environment": "",
            "activities": [],
            "objects": [],
            "interactions": [],
            "incident_indicators": [],
            "consistency_notes": "",
        }

        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Build incident-type-aware prompt context
            incident_context = ""
            if incident_type_id and incident_type_id in self.enhanced_rules:
                rules = self.enhanced_rules[incident_type_id]
                incident_context = (
                    f"\nExpected incident context: look especially for "
                    f"{', '.join(rules.get('expected_objects', []))} and "
                    f"actions like {', '.join(rules.get('expected_actions', []))}."
                )

            prompt = (
                "You are a forensic scene analyst. Analyze this image and reply ONLY with a "
                "JSON object (no markdown, no extra text) with these keys:\n"
                "- scene_description: one concise paragraph describing the scene factually\n"
                "- environment: one of [indoor, outdoor, street, market, residential, public, unknown]\n"
                "- activities: list of observable human activities (empty list if none)\n"
                "- objects: list of notable objects visible\n"
                "- interactions: list of notable person-person or person-object interactions\n"
                "- incident_indicators: list of any indicators that suggest an incident\n"
                "- consistency_notes: any observations about image consistency or possible tampering"
                + incident_context
            )

            payload = {
                "model": self.llava_model,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 512},
            }

            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            raw_text = resp.json().get("response", "")

            # Strip potential markdown code fences
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            llava_result = json.loads(raw_text)

            # Normalise types — model may return strings instead of lists
            for list_key in ("activities", "objects", "interactions", "incident_indicators"):
                val = llava_result.get(list_key, [])
                if isinstance(val, str):
                    llava_result[list_key] = [v.strip() for v in val.split(",") if v.strip()]
                elif not isinstance(val, list):
                    llava_result[list_key] = []

            for str_key in ("scene_description", "environment", "consistency_notes"):
                if not isinstance(llava_result.get(str_key), str):
                    llava_result[str_key] = ""

            return llava_result

        except requests.exceptions.ConnectionError:
            logger.warning("LLaVA: Ollama not reachable — skipping LLaVA analysis")
        except requests.exceptions.Timeout:
            logger.warning("LLaVA: request timed out — skipping LLaVA analysis")
        except json.JSONDecodeError as exc:
            logger.warning(f"LLaVA: could not parse JSON response — {exc}")
        except Exception as exc:
            logger.warning(f"LLaVA analysis failed: {exc}")

        return default

    def _merge_yolo_and_llava(
        self,
        yolo_objects: List[str],
        llava_result: Dict,
    ) -> Dict:
        """
        Cross-validate YOLO detections with LLaVA descriptions and produce:
        - consistency_score (0.0–1.0)
        - merged_objects (union with source tags)
        - combined_narrative (human-readable paragraph)
        """
        llava_objects_raw = [o.lower() for o in llava_result.get("objects", [])]
        yolo_set = {o.lower() for o in yolo_objects}
        llava_set = set(llava_objects_raw)

        # Overlap coefficient: |intersection| / min(|A|,|B|)
        if yolo_set and llava_set:
            intersection = yolo_set & llava_set
            overlap = len(intersection) / min(len(yolo_set), len(llava_set))
        elif not yolo_set and not llava_set:
            overlap = 1.0   # both empty → consistent
        else:
            overlap = 0.3   # one empty → partial consistency

        # Boost if scene description mentions YOLO objects
        scene_desc = llava_result.get("scene_description", "").lower()
        mentioned = sum(1 for obj in yolo_set if obj in scene_desc)
        scene_boost = min(0.2, mentioned * 0.05)

        consistency_score = min(1.0, overlap + scene_boost)

        # Merged object list with provenance tags
        merged = []
        for obj in yolo_set | llava_set:
            sources = []
            if obj in yolo_set:
                sources.append("YOLO")
            if obj in llava_set:
                sources.append("LLaVA")
            merged.append(f"{obj} [{'+'.join(sources)}]")

        # Build combined narrative
        parts = []
        scene_desc_text = llava_result.get("scene_description", "").strip()
        if scene_desc_text:
            parts.append(scene_desc_text)

        activities = llava_result.get("activities", [])
        if activities:
            parts.append("Observed activities: " + "; ".join(activities) + ".")

        interactions = llava_result.get("interactions", [])
        if interactions:
            parts.append("Notable interactions: " + "; ".join(interactions) + ".")

        incident_indicators = llava_result.get("incident_indicators", [])
        if incident_indicators:
            parts.append("Incident indicators: " + "; ".join(incident_indicators) + ".")

        if yolo_objects:
            parts.append(
                f"YOLO detection confirmed: {', '.join(yolo_objects[:6])}"
                + ("..." if len(yolo_objects) > 6 else "") + "."
            )

        consistency_label = (
            "high" if consistency_score >= 0.7
            else "moderate" if consistency_score >= 0.4
            else "low"
        )
        parts.append(
            f"Model consistency: {consistency_label} ({consistency_score:.2f}) — "
            + (
                "both models agree on scene content."
                if consistency_score >= 0.7
                else "minor discrepancies between YOLO and LLaVA; manual review recommended."
                if consistency_score >= 0.4
                else "significant discrepancy — treat evidence with caution."
            )
        )

        return {
            "consistency_score": round(consistency_score, 3),
            "merged_objects": merged,
            "combined_narrative": " ".join(parts),
        }

    def _generate_automated_report(self, analysis: 'EvidenceAnalysis') -> Dict:
        """Generate automated report summary and briefing"""
        report = {
            'summary': '',
            'key_points': [],
            'timeline_generated': False,
            'briefing': ''
        }
        
        try:
            # Generate summary
            summary_parts = []
            
            if analysis.has_people:
                summary_parts.append(f"{analysis.people_count} person(s) detected")
            
            if analysis.detected_objects:
                objects_str = ", ".join(analysis.detected_objects[:3])  # Top 3 objects
                summary_parts.append(f"Objects: {objects_str}")
            
            if analysis.detected_actions:
                actions_str = ", ".join(analysis.detected_actions)
                summary_parts.append(f"Actions: {actions_str}")
            
            if analysis.violence_detected:
                summary_parts.append("Violence indicators detected")
            
            if analysis.weapons_detected:
                weapons_str = ", ".join(analysis.weapons_detected)
                summary_parts.append(f"Weapons: {weapons_str}")
            
            report['summary'] = ". ".join(summary_parts) + "."
            
            # Generate key points
            report['key_points'] = []
            
            if analysis.confidence_score > 0.8:
                report['key_points'].append("High confidence evidence")
            elif analysis.confidence_score < 0.4:
                report['key_points'].append("Low confidence - requires verification")
            
            if analysis.is_anomalous:
                report['key_points'].append("Unusual patterns detected")
            
            if analysis.tamper_detected:
                report['key_points'].append("Evidence tampering suspected")
            
            if analysis.violence_detected:
                report['key_points'].append("Violent incident confirmed")
            
            if analysis.document_forgery_detected:
                report['key_points'].append("Potential document forgery")
            
            # Generate officer briefing
            briefing_parts = []
            
            briefing_parts.append(f"Evidence Quality Score: {analysis.quality_score:.2f}")
            
            if analysis.faces_detected > 0:
                if analysis.privacy_blurred:
                    briefing_parts.append(f"{analysis.faces_detected} face(s) detected and blurred for privacy")
                else:
                    briefing_parts.append(f"{analysis.faces_detected} face(s) detected - privacy review needed")
            
            if analysis.scene_confidence > 0.7:
                briefing_parts.append(f"Scene identified: {analysis.scene_type} ({analysis.lighting_condition} lighting)")
            
            if analysis.is_anomalous:
                briefing_parts.append("ANOMALY ALERT: " + "; ".join(analysis.anomaly_reasons))
            
            if crossref_count := getattr(analysis, 'similar_reports_count', 0):
                briefing_parts.append(f"{crossref_count} similar reports in area")

            # LLaVA combined analysis — most detailed section
            if getattr(analysis, 'combined_analysis', ''):
                briefing_parts.append("\n--- AI Scene Analysis (LLaVA + YOLO) ---")
                briefing_parts.append(analysis.combined_analysis)

            if getattr(analysis, 'llava_interactions', []):
                briefing_parts.append(
                    "Interactions observed: " + "; ".join(analysis.llava_interactions)
                )

            consistency = getattr(analysis, 'yolo_llava_consistency', None)
            if consistency is not None:
                flag = "" if consistency >= 0.7 else " [REVIEW NEEDED]"
                briefing_parts.append(
                    f"YOLO–LLaVA consistency: {consistency:.0%}{flag}"
                )

            report['briefing'] = "\n".join(briefing_parts)
            report['timeline_generated'] = bool(analysis.exif_timestamp)
            
        except Exception as e:
            logger.warning(f"Automated report generation failed: {e}")
        
        return report
    
    def _classify_scene(self, image: np.ndarray, detected_objects: List[str]) -> str:
        """Classify scene type based on content"""
        try:
            if 'person' in detected_objects or 'people' in detected_objects:
                if 'structure' in detected_objects:
                    return 'indoor'
                else:
                    return 'outdoor'
            elif 'vehicle' in detected_objects:
                return 'street'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _check_exif_data(self, image: Image.Image) -> bool:
        """Check if EXIF data is complete and valid"""
        try:
            exif = image._getexif()
            if exif is None:
                return False
            
            required_tags = ['DateTimeOriginal', 'Make', 'Model']
            for tag in required_tags:
                if tag not in exif:
                    return False
            
            return True
        except:
            return False
    
    def _calculate_confidence_score(self, analysis: EvidenceAnalysis) -> float:
        """Calculate overall confidence score for evidence quality"""
        score = 0.0
        
        # People detection (important for most incident types)
        if analysis.has_people:
            score += 0.2
        
        # Image quality
        if not analysis.is_blurry:
            score += 0.2
        
        # Brightness (not too dark or too bright)
        if 0.2 <= analysis.brightness <= 0.8:
            score += 0.1
        
        # Text presence (can provide context)
        if analysis.has_text:
            score += 0.1
        
        # EXIF data (authenticity)
        if analysis.exif_complete:
            score += 0.1
        
        # Resolution (minimum quality)
        if analysis.resolution[0] >= 640 and analysis.resolution[1] >= 480:
            score += 0.1
        
        # File size (indicates quality)
        if analysis.file_size > 50000:
            score += 0.1
        
        # Object detection
        if analysis.detected_objects and 'unknown' not in analysis.detected_objects:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_advanced_confidence_score(self, analysis: EvidenceAnalysis) -> float:
        """Calculate advanced confidence score using all features"""
        score = 0.0
        
        # Basic confidence (40% weight)
        basic_score = self._calculate_confidence_score(analysis)
        score += basic_score * 0.4
        
        # Action detection confidence (15% weight)
        if analysis.detected_actions:
            score += analysis.action_confidence * 0.15
        
        # Scene context confidence (10% weight)
        score += analysis.scene_confidence * 0.1
        
        # Violence detection (10% weight)
        if analysis.violence_detected:
            score += analysis.violence_confidence * 0.1
        
        # Multi-modal consistency (10% weight)
        score += analysis.cross_modal_consistency * 0.1
        
        # Quality score (15% weight)
        score += analysis.quality_score * 0.15
        
        # Penalty factors
        if analysis.is_anomalous:
            score -= 0.2
        
        if analysis.tamper_detected:
            score -= 0.3
        
        if not analysis.timestamp_valid:
            score -= 0.1
        
        if not analysis.chain_valid:
            score -= 0.2
        
        return max(min(score, 1.0), 0.0)
    
    def validate_incident_evidence(
        self,
        incident_type_id: int,
        description: str,
        analysis: EvidenceAnalysis,
        *,
        media_type: str = "photo",
    ) -> Dict:
        """Advanced evidence validation against incident type requirements (photo/video/audio)."""
        logger.info(f"Advanced validation for incident type {incident_type_id}")
        
        rules_bundle = self._get_rules_for_incident(incident_type_id)
        ev = rules_bundle.get("evidence_rules", {}) if isinstance(rules_bundle, dict) else {}
        allowed = ev.get("allowed_media_types", ["photo", "video", "audio"])
        if media_type and media_type not in allowed:
            return {
                "valid": False,
                "reason": "media_type_not_allowed",
                "confidence": 0.0,
                "issues": [f"Media type '{media_type}' not allowed for this incident type"],
                "warnings": [],
                "advanced_analysis": {"media_type": media_type, "allowed_media_types": allowed},
            }

        # Get evidence rules for this incident type
        rules = ev.get("rule", {}) if isinstance(ev.get("rule"), dict) else {}
        
        if not rules:
            return {
                'valid': False,
                'reason': 'Unknown incident type',
                'confidence': 0.0,
                'issues': ['Unknown incident type'],
                'advanced_analysis': {}
            }
        
        score = 0.0
        max_score = 0.0
        issues = []
        warnings = []
        
        # === CORE VALIDATION (50% weight) ===
        
        # 1. Expected objects (15% weight)
        if 'expected_objects' in rules:
            max_score += 0.15
            object_matches = 0
            for obj in rules['expected_objects']:
                if obj in analysis.detected_objects:
                    object_matches += 1
            
            if object_matches > 0:
                score += 0.15 * (object_matches / len(rules['expected_objects']))
            else:
                issues.append(f"No expected objects found. Expected: {rules['expected_objects']}")
        
        # 2. People detection (10% weight)
        max_score += 0.1
        if analysis.has_people:
            score += 0.1
        else:
            issues.append("No people detected in evidence")
        
        # 3. Action validation (15% weight)
        max_score += 0.15
        if 'expected_actions' in rules and analysis.detected_actions:
            action_matches = 0
            for action in rules['expected_actions']:
                if action in analysis.detected_actions:
                    action_matches += 1
            
            if action_matches > 0:
                score += 0.15 * (action_matches / len(rules['expected_actions']))
            else:
                warnings.append(f"No expected actions detected. Expected: {rules['expected_actions']}")
        else:
            warnings.append("No actions detected in evidence")
        
        # 4. Scene validation (10% weight)
        max_score += 0.1
        if 'expected_scenes' in rules:
            scene_match = False
            for scene in rules['expected_scenes']:
                if scene in analysis.scene_type or (scene == 'market' and 'market' in description.lower()):
                    scene_match = True
                    break
            
            if scene_match or analysis.scene_confidence > 0.7:
                score += 0.1
            else:
                warnings.append(f"Scene mismatch. Expected: {rules['expected_scenes']}, Found: {analysis.scene_type}")
        
        # === QUALITY & AUTHENTICITY (30% weight) ===
        
        # 5. Technical quality (10% weight)
        max_score += 0.1
        if analysis.technical_quality > 0.7:
            score += 0.1
        elif analysis.technical_quality > 0.5:
            score += 0.05
        else:
            warnings.append("Low technical quality")
        
        # 6. Content quality (10% weight)
        max_score += 0.1
        if analysis.content_quality > 0.7:
            score += 0.1
        elif analysis.content_quality > 0.5:
            score += 0.05
        else:
            warnings.append("Low content quality")
        
        # 7. Authenticity (10% weight)
        max_score += 0.1
        if analysis.authenticity_score > 0.8:
            score += 0.1
        elif analysis.authenticity_score > 0.6:
            score += 0.05
        else:
            if analysis.tamper_detected:
                issues.append("Evidence tampering detected")
            if not analysis.chain_valid:
                issues.append("Evidence chain validation failed")
            if not analysis.timestamp_valid:
                warnings.append("Timestamp validation failed")
        
        # === ADVANCED VALIDATION (20% weight) ===
        
        # 8. Violence detection (for applicable incidents)
        max_score += 0.05
        if incident_type_id in [2, 5]:  # Assault, Domestic Violence
            if analysis.violence_detected:
                score += 0.05
            else:
                warnings.append("No violence indicators detected for violent incident type")
        else:
            score += 0.05  # Not applicable, give full points
        
        # 9. Multi-modal consistency (5% weight)
        max_score += 0.05
        if analysis.cross_modal_consistency > 0.7:
            score += 0.05
        elif analysis.cross_modal_consistency > 0.5:
            score += 0.025
        else:
            warnings.append("Low multi-modal consistency")
        
        # 10. Anomaly check (5% weight)
        max_score += 0.05
        if not analysis.is_anomalous:
            score += 0.05
        else:
            issues.extend(analysis.anomaly_reasons)
        
        # 11. Privacy compliance (5% weight)
        max_score += 0.05
        if analysis.faces_detected > 0:
            if analysis.privacy_blurred:
                score += 0.05
            else:
                warnings.append("Faces detected but not blurred - privacy concern")
        else:
            score += 0.05
        
        # === DESCRIPTION ANALYSIS ===
        
        # 12. Keyword matching (bonus points)
        description_lower = description.lower()
        keyword_matches = 0
        if 'keywords' in rules:
            for keyword in rules['keywords']:
                if keyword in description_lower:
                    keyword_matches += 1
            
            if keyword_matches > 0:
                bonus = 0.1 * (keyword_matches / len(rules['keywords']))
                score += bonus
                max_score += bonus
        
        # Calculate final score
        final_score = score / max_score if max_score > 0 else 0.0
        analysis.rule_based_score = round(final_score, 3)
        
        # Determine validation result with dynamic threshold
        base_threshold = 0.6
        threshold = base_threshold  # Initialize threshold
        
        # Adjust threshold based on incident severity and evidence quality
        if incident_type_id in [2, 5]:  # High severity incidents
            threshold = base_threshold - 0.1  # More lenient for serious incidents
        
        if analysis.authenticity_score < 0.5:
            threshold = base_threshold + 0.2  # Stricter for suspicious evidence
        
        if analysis.violence_detected and incident_type_id in [2, 5]:
            threshold = base_threshold - 0.1  # More lenient if violence detected
        
        is_valid = final_score >= threshold
        
        # Prepare advanced analysis summary
        advanced_analysis = {
            'actions_detected': analysis.detected_actions,
            'violence_detected': analysis.violence_detected,
            'weapons_detected': analysis.weapons_detected,
            'yolo_structured_features': {
                'object_counts': analysis.yolo_object_counts,
                'presence_flags': analysis.yolo_presence_flags,
                'high_risk_objects': analysis.yolo_high_risk_objects,
                'feature_score': analysis.yolo_feature_score,
            },
            'llava_structured_features': {
                'scene_label': analysis.llava_scene_label,
                'activity_scores': analysis.llava_activity_scores,
                'interaction_complexity_score': analysis.llava_interaction_complexity,
                'environment_label': analysis.llava_environment_label or analysis.llava_environment,
                'feature_score': analysis.llava_feature_score,
            },
            'faces_detected': analysis.faces_detected,
            'privacy_blurred': analysis.privacy_blurred,
            'scene_context': {
                'is_indoor': analysis.is_indoor,
                'lighting': analysis.lighting_condition,
                'weather': analysis.weather_condition
            },
            'quality_scores': {
                'technical': analysis.technical_quality,
                'content': analysis.content_quality,
                'authenticity': analysis.authenticity_score,
                'overall': analysis.quality_score
            },
            'anomaly_detected': analysis.is_anomalous,
            'tamper_detected': analysis.tamper_detected,
            'chain_valid': analysis.chain_valid
        }
        
        decision_label = getattr(analysis, "decision_label", "") or "REJECTED"
        decision_trust = getattr(analysis, "decision_trust_score", final_score)
        decision_breakdown = getattr(analysis, "decision_breakdown", {})
        workflow_decision = str(decision_breakdown.get("workflow_decision") or "REJECTED")
        is_valid = workflow_decision == "ACCEPTED"
        feature_summary = {
            'yolo_objects': analysis.detected_objects,
            'yolo_object_counts': analysis.yolo_object_counts,
            'yolo_presence_flags': analysis.yolo_presence_flags,
            'llava_scene': analysis.llava_scene_label or analysis.llava_scene_description,
            'llava_actions': analysis.llava_activities,
            'llava_activity_scores': analysis.llava_activity_scores,
            'high_risk_objects': analysis.yolo_high_risk_objects,
            'environment_label': analysis.llava_environment_label or analysis.llava_environment,
            'interaction_complexity_score': round(analysis.llava_interaction_complexity, 3),
        }
        decision_details = {
            'label': decision_label,
            'decision': workflow_decision,
            'trust_score': decision_trust,
            'xgboost_score': getattr(analysis, 'xgboost_score', decision_trust),
            'semantic_match_score': getattr(analysis, 'semantic_match_score', 0.0),
            'rule_based_score': getattr(analysis, 'rule_based_score', final_score),
            'consistency_score': decision_breakdown.get('consistency_score', getattr(analysis, 'semantic_match_score', 0.0)),
            'similarity_score': decision_breakdown.get('similarity_score', getattr(analysis, 'desc_vs_llava_similarity', 0.0)),
            'evidence_match_score': decision_breakdown.get('evidence_match_score', 0.0),
            'contradiction': bool(decision_breakdown.get('contradiction', False)),
            'ai_score': decision_breakdown.get('ai_score', 0.0),
            'rule_score': decision_breakdown.get('rule_score_final', 0.0),
            'final_score': decision_breakdown.get('final_score', decision_trust * 100),
            'yolo_feature_score': getattr(analysis, 'yolo_feature_score', 0.0),
            'llava_feature_score': getattr(analysis, 'llava_feature_score', 0.0),
            'anomaly_score': getattr(analysis, 'anomaly_risk_score', 0.0),
            'evidence_quality_score': getattr(analysis, 'evidence_quality_score', analysis.quality_score),
            'feature_summary': feature_summary,
            'reasoning': getattr(analysis, 'decision_reasoning', ''),
            'breakdown': decision_breakdown,
            'final_verdict_reason': getattr(analysis, 'final_verdict_reason', ''),
            'xgboost_probabilities': getattr(analysis, 'xgboost_probabilities', {}),
        }

        return {
            'decision': workflow_decision,
            'legacy_decision': decision_label,
            'final_score': decision_details['final_score'],
            'ai_score': decision_details['ai_score'],
            'rule_score': decision_details['rule_score'],
            'trust_score': decision_trust,
            'xgboost_score': decision_details['xgboost_score'],
            'semantic_match_score': decision_details['semantic_match_score'],
            'rule_based_score': decision_details['rule_based_score'],
            'yolo_feature_score': decision_details['yolo_feature_score'],
            'llava_feature_score': decision_details['llava_feature_score'],
            'anomaly_score': decision_details['anomaly_score'],
            'evidence_quality_score': decision_details['evidence_quality_score'],
            'details': {
                'consistency_score': decision_details['consistency_score'],
                'similarity_score': decision_details['similarity_score'],
                'evidence_match_score': decision_details['evidence_match_score'],
                'contradiction': decision_details['contradiction'],
            },
            'feature_summary': feature_summary,
            'final_verdict_reason': decision_details['final_verdict_reason'],
            'reason': decision_details['final_verdict_reason'],
            'valid': is_valid,
            'confidence': final_score,
            'threshold_used': threshold,
            'issues': issues,
            'warnings': warnings,
            'advanced_analysis': advanced_analysis,
            'analysis_summary': {
                'has_people': analysis.has_people,
                'detected_objects': analysis.detected_objects,
                'extracted_text': analysis.extracted_text,
                'quality_score': analysis.quality_score
            },
            'decision_details': decision_details,
            'incident_verification': decision_details,
        }

def analyze_text_only_report(description: str, incident_type_name: str, incident_type_id: int) -> Dict:
    """
    Analyze text-only reports using NLP and rule-based validation
    """
    if not description or not description.strip():
        return {
            'valid': False,
            'confidence': 0.0,
            'threshold_used': 0.6,
            'issues': ['No description provided'],
            'warnings': ['Text-only report requires detailed description'],
            'advanced_analysis': {
                'text_analysis': True,
                'description_quality': 'poor',
                'incident_type_match': False
            },
            'analysis_summary': {
                'text_length': 0,
                'word_count': 0,
                'credibility_indicators': []
            }
        }
    
    # Text quality metrics
    text_length = len(description.strip())
    word_count = len(description.split())
    
    # Initialize analysis variables
    score = 0.0
    max_score = 1.0
    issues = []
    warnings = []
    credibility_indicators = []
    
    # 1. Description length analysis (0.3 points)
    if text_length >= 50:
        score += 0.3
        credibility_indicators.append('adequate_length')
    elif text_length >= 20:
        score += 0.15
        warnings.append('Description could be more detailed')
    else:
        issues.append('Description too short for meaningful analysis')
    
    # 2. Word count analysis (0.2 points)
    if word_count >= 10:
        score += 0.2
        credibility_indicators.append('detailed_narrative')
    elif word_count >= 5:
        score += 0.1
    else:
        warnings.append('Very brief description')
    
    # 3. Incident type specific keywords (0.3 points)
    incident_keywords = {
        'theft': ['stole', 'theft', 'stolen', 'took', 'robbed', 'pickpocket', 'burglary', 'shoplifting'],
        'assault': ['hit', 'attacked', 'assaulted', 'fight', 'violence', 'beating', 'punched', 'threatened'],
        'vandalism': ['damaged', 'broke', 'vandalized', 'destroyed', 'graffiti', 'smashed', 'property damage'],
        'suspicious': ['suspicious', 'strange', 'unusual', 'loitering', 'watching', 'following', 'weird'],
        'harassment': ['harassed', 'threatened', 'bullied', 'intimidated', 'unwanted', 'inappropriate', 'stalking'],
        'traffic': ['accident', 'crash', 'collision', 'speeding', 'reckless', 'drunk driving', 'traffic violation']
    }
    
    description_lower = description.lower()
    keyword_matches = 0
    
    if incident_type_name.lower() in incident_keywords:
        keywords = incident_keywords[incident_type_name.lower()]
        for keyword in keywords:
            if keyword in description_lower:
                keyword_matches += 1
        
        if keyword_matches >= 2:
            score += 0.3
            credibility_indicators.append('relevant_keywords')
        elif keyword_matches >= 1:
            score += 0.15
        else:
            warnings.append('Description lacks incident-specific details')
    
    # 4. Credibility indicators (0.2 points)
    credibility_phrases = [
        'i saw', 'i witnessed', 'i heard', 'happened in front of me', 'clearly visible',
        'immediately', 'called police', 'reported to', 'emergency services'
    ]
    
    phrase_matches = sum(1 for phrase in credibility_phrases if phrase in description_lower)
    if phrase_matches >= 2:
        score += 0.2
        credibility_indicators.append('first_hand_account')
    elif phrase_matches >= 1:
        score += 0.1
    
    # 5. Red flags (negative scoring)
    red_flags = ['fake', 'joke', 'prank', 'testing', 'just kidding', 'not real', 'fabricated']
    red_flag_count = sum(1 for flag in red_flags if flag in description_lower)
    
    if red_flag_count > 0:
        score -= 0.3 * red_flag_count
        issues.append(f'Suspicious language detected: {red_flag_count} red flags')
    
    # 6. Time and location indicators (bonus 0.1)
    time_location_indicators = ['today', 'yesterday', 'morning', 'evening', 'night', 'at', 'near', 'location']
    tl_matches = sum(1 for indicator in time_location_indicators if indicator in description_lower)
    if tl_matches >= 2:
        score += 0.1
        credibility_indicators.append('temporal_spatial_context')
    
    # Calculate final score
    final_score = max(0.0, min(1.0, score))
    
    # Determine validation result
    base_threshold = 0.5  # Lower threshold for text-only reports
    
    # Adjust threshold based on incident severity
    if incident_type_id in [2, 5]:  # High severity incidents
        base_threshold = 0.4  # More lenient for serious incidents
    
    is_valid = final_score >= base_threshold
    
    # Determine description quality
    if final_score >= 0.8:
        quality = 'excellent'
    elif final_score >= 0.6:
        quality = 'good'
    elif final_score >= 0.4:
        quality = 'fair'
    else:
        quality = 'poor'
    
    return {
        'valid': is_valid,
        'confidence': final_score,
        'threshold_used': base_threshold,
        'issues': issues,
        'warnings': warnings,
        'advanced_analysis': {
            'text_analysis': True,
            'description_quality': quality,
            'incident_type_match': keyword_matches >= 1,
            'credibility_indicators': credibility_indicators,
            'red_flags_detected': red_flag_count
        },
        'analysis_summary': {
            'text_length': text_length,
            'word_count': word_count,
            'keyword_matches': keyword_matches,
            'credibility_indicators': credibility_indicators
        }
    }

# Global service instance
evidence_analysis_service = EvidenceAnalysisService()
