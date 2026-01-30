"""
Report Comments API Routes.

Provides endpoints for:
- Adding comments/updates to reports
- Viewing comment history
- Managing case notes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import (
    Report, ReportStatus, User, UserRole,
    ReportComment, CommentType, CommentVisibility
)
from app.models.report_comment import add_comment, add_status_change_comment
from datetime import datetime

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/report/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_comments(report_id):
    """Get all comments for a report."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check access permissions
    is_reporter = report.reporter_id == user_id
    is_staff = user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]
    
    if not is_reporter and not is_staff:
        return jsonify({'error': 'Access denied'}), 403
    
    # Build query based on visibility
    query = ReportComment.query.filter(
        ReportComment.report_id == report_id,
        ReportComment.parent_id.is_(None)  # Top-level comments only
    )
    
    # Citizens can only see reporter-visible and public comments
    if not is_staff:
        query = query.filter(
            ReportComment.visibility.in_([
                CommentVisibility.REPORTER,
                CommentVisibility.PUBLIC
            ])
        )
    
    comments = query.order_by(ReportComment.created_at.desc()).all()
    
    return jsonify({
        'comments': [c.to_dict() for c in comments],
        'total': len(comments)
    }), 200


@comments_bp.route('/report/<int:report_id>', methods=['POST'])
@jwt_required()
def add_report_comment(report_id):
    """Add a comment to a report."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check permissions
    is_reporter = report.reporter_id == user_id
    is_staff = user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]
    
    if not is_reporter and not is_staff:
        return jsonify({'error': 'Access denied'}), 403
    
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    # Determine visibility
    if is_staff:
        visibility_str = data.get('visibility', 'internal')
        visibility = CommentVisibility(visibility_str)
    else:
        # Citizens can only create reporter-visible comments
        visibility = CommentVisibility.REPORTER
    
    # Determine comment type
    comment_type_str = data.get('type', 'note')
    try:
        comment_type = CommentType(comment_type_str)
    except ValueError:
        comment_type = CommentType.NOTE
    
    comment = add_comment(
        report=report,
        user=user,
        content=content,
        comment_type=comment_type,
        visibility=visibility,
        attachments=data.get('attachments', [])
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment': comment.to_dict()
    }), 201


@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Update a comment."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    comment = ReportComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Only author or admin can edit
    if comment.author_id != user_id and user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Access denied'}), 403
    
    if data.get('content'):
        comment.content = data['content']
        comment.is_edited = True
    
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if data.get('visibility'):
            comment.visibility = CommentVisibility(data['visibility'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Comment updated successfully',
        'comment': comment.to_dict()
    }), 200


@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    comment = ReportComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Only author or admin can delete
    if comment.author_id != user_id and user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete replies first
    ReportComment.query.filter(ReportComment.parent_id == comment_id).delete()
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200


@comments_bp.route('/<int:comment_id>/reply', methods=['POST'])
@jwt_required()
def reply_to_comment(comment_id):
    """Add a reply to a comment."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    parent_comment = ReportComment.query.get(comment_id)
    if not parent_comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    report = parent_comment.report
    
    # Check permissions
    is_reporter = report.reporter_id == user_id
    is_staff = user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]
    
    if not is_reporter and not is_staff:
        return jsonify({'error': 'Access denied'}), 403
    
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Reply content is required'}), 400
    
    reply = ReportComment(
        report_id=report.id,
        author_id=user.id,
        author_name=f"{user.first_name} {user.last_name}",
        author_role=user.role.value,
        content=content,
        comment_type=parent_comment.comment_type,
        visibility=parent_comment.visibility,
        parent_id=comment_id
    )
    
    db.session.add(reply)
    db.session.commit()
    
    return jsonify({
        'message': 'Reply added successfully',
        'comment': reply.to_dict()
    }), 201


# ==================== Status Update with Comment ====================

@comments_bp.route('/report/<int:report_id>/status', methods=['POST'])
@jwt_required()
def update_status_with_comment(report_id):
    """Update report status with a comment."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OFFICER]:
        return jsonify({'error': 'Staff access required'}), 403
    
    data = request.get_json()
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    new_status_str = data.get('status')
    if not new_status_str:
        return jsonify({'error': 'New status is required'}), 400
    
    try:
        new_status = ReportStatus(new_status_str)
    except ValueError:
        return jsonify({'error': 'Invalid status'}), 400
    
    old_status = report.status.value
    note = data.get('note', '')
    
    # Update report status
    report.status = new_status
    
    # Update status history
    history = report.status_history or []
    history.append({
        'status': new_status.value,
        'timestamp': datetime.utcnow().isoformat(),
        'updatedBy': user_id,
        'note': note
    })
    report.status_history = history
    
    if new_status == ReportStatus.RESOLVED:
        report.resolved_at = datetime.utcnow()
        if data.get('resolutionNotes'):
            report.resolution_notes = data['resolutionNotes']
    
    # Add status change comment
    comment = add_status_change_comment(
        report=report,
        user=user,
        old_status=old_status,
        new_status=new_status.value,
        note=note
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Status updated successfully',
        'report': report.to_dict(include_reporter=False),
        'comment': comment.to_dict()
    }), 200
