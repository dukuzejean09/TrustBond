"""
Feedback Routes - App feedback management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import FeedbackService, PoliceService

feedback_bp = Blueprint('feedback', __name__)


# ==================== MOBILE APP ENDPOINTS ====================
@feedback_bp.route('/submit', methods=['POST'])
def submit_feedback():
    """Submit feedback from mobile app (no auth required)"""
    data = request.get_json()
    
    if not data.get('feedback_type') or not data.get('content'):
        return jsonify({'error': 'feedback_type and content are required'}), 400
    
    try:
        feedback = FeedbackService.create_feedback({
            'device_id': data.get('device_id'),
            'feedback_type': data['feedback_type'],
            'subject': data.get('subject'),
            'content': data['content'],
            'contact_email': data.get('contact_email'),
            'contact_phone': data.get('contact_phone'),
            'contact_consent': data.get('contact_consent', False),
            'app_version': data.get('app_version'),
            'os_version': data.get('os_version'),
            'device_model': data.get('device_model'),
            'platform': data.get('platform'),
            'screen_name': data.get('screen_name'),
            'error_logs': data.get('error_logs'),
            'steps_to_reproduce': data.get('steps_to_reproduce'),
            'rating': data.get('rating'),
            'metadata': data.get('metadata')
        })
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.feedback_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to submit feedback'}), 500


# ==================== ADMIN ENDPOINTS ====================
@feedback_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_feedback():
    """Get all feedback with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {}
    if request.args.get('feedback_type'):
        filters['feedback_type'] = request.args.get('feedback_type')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('device_id'):
        filters['device_id'] = request.args.get('device_id')
    if request.args.get('app_version'):
        filters['app_version'] = request.args.get('app_version')
    if request.args.get('platform'):
        filters['platform'] = request.args.get('platform')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    pagination = FeedbackService.get_all_feedback(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'feedback': [FeedbackService.feedback_to_dict(f) for f in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@feedback_bp.route('/unresolved', methods=['GET'])
@jwt_required()
def get_unresolved_feedback():
    """Get all unresolved feedback"""
    feedback_list = FeedbackService.get_unresolved_feedback()
    
    return jsonify({
        'feedback': [FeedbackService.feedback_to_dict(f) for f in feedback_list]
    }), 200


@feedback_bp.route('/high-priority', methods=['GET'])
@jwt_required()
def get_high_priority_feedback():
    """Get high/critical priority unresolved feedback"""
    feedback_list = FeedbackService.get_high_priority_feedback()
    
    return jsonify({
        'feedback': [FeedbackService.feedback_to_dict(f) for f in feedback_list]
    }), 200


@feedback_bp.route('/<feedback_id>', methods=['GET'])
@jwt_required()
def get_feedback(feedback_id):
    """Get feedback details"""
    feedback = FeedbackService.get_feedback_by_id(feedback_id)
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'feedback': FeedbackService.feedback_to_dict(feedback, include_attachments=True)
    }), 200


@feedback_bp.route('/<feedback_id>', methods=['PUT'])
@jwt_required()
def update_feedback(feedback_id):
    """Update feedback record"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    feedback = FeedbackService.update_feedback(
        feedback_id=feedback_id,
        update_data=data,
        updated_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Feedback updated successfully',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


@feedback_bp.route('/<feedback_id>/assign', methods=['POST'])
@jwt_required()
def assign_feedback(feedback_id):
    """Assign feedback to a user"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('assigned_to'):
        return jsonify({'error': 'assigned_to is required'}), 400
    
    feedback = FeedbackService.assign_feedback(
        feedback_id=feedback_id,
        user_id=data['assigned_to'],
        assigned_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Feedback assigned successfully',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


@feedback_bp.route('/<feedback_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_feedback(feedback_id):
    """Mark feedback as resolved"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    feedback = FeedbackService.resolve_feedback(
        feedback_id=feedback_id,
        resolution_notes=data.get('resolution_notes'),
        resolved_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Feedback resolved successfully',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


@feedback_bp.route('/<feedback_id>/close', methods=['POST'])
@jwt_required()
def close_feedback(feedback_id):
    """Close feedback without resolution"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    feedback = FeedbackService.close_feedback(
        feedback_id=feedback_id,
        reason=data.get('reason'),
        closed_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Feedback closed',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


@feedback_bp.route('/<feedback_id>/wont-fix', methods=['POST'])
@jwt_required()
def wont_fix_feedback(feedback_id):
    """Mark feedback as won't fix"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('reason'):
        return jsonify({'error': 'reason is required'}), 400
    
    feedback = FeedbackService.mark_wont_fix(
        feedback_id=feedback_id,
        reason=data['reason'],
        marked_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Feedback marked as won\'t fix',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


@feedback_bp.route('/<feedback_id>/priority', methods=['PUT'])
@jwt_required()
def set_priority(feedback_id):
    """Set feedback priority"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('priority'):
        return jsonify({'error': 'priority is required'}), 400
    
    feedback = FeedbackService.set_priority(
        feedback_id=feedback_id,
        priority=data['priority'],
        set_by_user_id=user_id
    )
    
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404
    
    return jsonify({
        'message': 'Priority updated',
        'feedback': FeedbackService.feedback_to_dict(feedback)
    }), 200


# ==================== STATISTICS ====================
@feedback_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_feedback_statistics():
    """Get feedback statistics"""
    days = request.args.get('days', 30, type=int)
    
    stats = FeedbackService.get_feedback_stats(days=days)
    
    return jsonify(stats), 200


@feedback_bp.route('/statistics/versions', methods=['GET'])
@jwt_required()
def get_version_statistics():
    """Get feedback by app version"""
    days = request.args.get('days', 30, type=int)
    
    stats = FeedbackService.get_app_version_stats(days=days)
    
    return jsonify({
        'version_stats': stats
    }), 200


@feedback_bp.route('/statistics/platforms', methods=['GET'])
@jwt_required()
def get_platform_statistics():
    """Get feedback by platform"""
    days = request.args.get('days', 30, type=int)
    
    stats = FeedbackService.get_platform_stats(days=days)
    
    return jsonify({
        'platform_stats': stats
    }), 200
