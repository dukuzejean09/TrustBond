"""Background tasks for processing reports."""
import logging
from typing import Dict, Any
from datetime import datetime, timezone

from sqlalchemy import or_

from app.database import SessionLocal
from app.models.report import Report
from app.utils.ml_evaluator import ml_evaluator
from app.core.incident_grouping import sync_incident_groups
from app.api.v1.reports import _create_auto_cases

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def process_single_report(report: Report) -> Dict[str, Any]:
    """Process a single report through ML evaluation."""
    result = {
        "report_id": str(report.report_id),
        "trust_score": None,
        "status": "success",
    }
    
    try:
        # Run ML evaluation
        ml_result = ml_evaluator.evaluate_report(report)
        trust_score = float(ml_result['trust_score'])
        
        # Update report with AI results
        report.feature_vector = {
            'trust_score': trust_score,
            'prediction_label': ml_result['prediction_label'],
            'confidence': float(ml_result['confidence']),
            'reasoning': ml_result['reasoning']
        }
        report.ai_ready = True
        report.features_extracted_at = datetime.now(timezone.utc)
        
        # Auto-verify/reject based on trust score
        if trust_score >= 70.0:
            report.verification_status = 'verified'
            report.status = 'verified'
            report.rule_status = 'passed'
            result["action"] = "verified"
        elif trust_score < 30.0:
            report.verification_status = 'rejected'
            report.status = 'rejected'
            report.rule_status = 'failed'
            result["action"] = "rejected"
        else:
            report.verification_status = 'under_review'
            report.rule_status = 'pending'
            result["action"] = "under_review"
        
        result["trust_score"] = trust_score
        
    except Exception as e:
        logger.error(f"Error processing report {report.report_id}: {e}")
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


def process_pending_reports(batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """
    Process pending reports through ML evaluation.
    This is a Celery task that processes reports in the background.
    """
    stats = {
        "processed": 0,
        "verified": 0,
        "rejected": 0,
        "under_review": 0,
        "errors": 0,
    }
    
    db = SessionLocal()
    try:
        # Get pending reports (not yet AI-processed)
        pending_reports = db.query(Report).filter(
            or_(
                Report.ai_ready.is_(None),
                Report.ai_ready == False
            ),
            Report.verification_status.in_(['pending', 'under_review'])
        ).limit(batch_size).all()
        
        logger.info(f"Found {len(pending_reports)} pending reports to process")
        
        for report in pending_reports:
            result = process_single_report(report)
            stats["processed"] += 1
            
            if result.get("status") == "error":
                stats["errors"] += 1
            elif result.get("action") == "verified":
                stats["verified"] += 1
            elif result.get("action") == "rejected":
                stats["rejected"] += 1
            else:
                stats["under_review"] += 1
        
        db.commit()
        
        # Run incident grouping and case creation if any reports were verified
        if stats["verified"] > 0:
            logger.info(f"Running incident grouping after processing {stats['verified']} verified reports")
            group_stats = sync_incident_groups(db)
            logger.info(f"Incident groups: {group_stats.get('created', 0)} created, {group_stats.get('updated', 0)} updated")
            
            case_stats = _create_auto_cases(db)
            logger.info(f"Auto-cases created: {case_stats.get('cases_created', 0)}")
        
        logger.info(f"Report processing completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in process_pending_reports: {e}")
        db.rollback()
        stats["errors"] += 1
        return stats
    finally:
        db.close()


def process_all_pending_reports() -> Dict[str, Any]:
    """
    Process all pending reports (no batch limit).
    Use with caution for large datasets.
    """
    total_stats = {
        "total_processed": 0,
        "batches": 0,
        "verified": 0,
        "rejected": 0,
        "under_review": 0,
        "errors": 0,
    }
    
    while True:
        batch_stats = process_pending_reports(batch_size=BATCH_SIZE)
        total_stats["batches"] += 1
        total_stats["total_processed"] += batch_stats["processed"]
        total_stats["verified"] += batch_stats["verified"]
        total_stats["rejected"] += batch_stats["rejected"]
        total_stats["under_review"] += batch_stats["under_review"]
        total_stats["errors"] += batch_stats["errors"]
        
        # Check if there are more pending reports
        if batch_stats["processed"] < BATCH_SIZE:
            break
    
    logger.info(f"All pending reports processed: {total_stats}")
    return total_stats


# For direct invocation (non-Celery)
if __name__ == "__main__":
    result = process_pending_reports()
    print(f"Result: {result}")