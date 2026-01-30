"""
Verification Routes - Verification rules management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import VerificationService, AuditService

verification_bp = Blueprint('verification', __name__)


# ==================== RULE MANAGEMENT ====================
@verification_bp.route('/rules', methods=['GET'])
@jwt_required()
def get_all_rules():
    """Get all verification rules"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    rules = VerificationService.get_all_rules(include_inactive=include_inactive)
    
    return jsonify({
        'rules': [VerificationService.rule_to_dict(r) for r in rules]
    }), 200


@verification_bp.route('/rules/<int:rule_id>', methods=['GET'])
@jwt_required()
def get_rule(rule_id):
    """Get rule details"""
    rule = VerificationService.get_rule_by_id(rule_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify({
        'rule': VerificationService.rule_to_dict(rule)
    }), 200


@verification_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_rule():
    """Create a new verification rule"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('rule_name') or not data.get('rule_code'):
        return jsonify({'error': 'rule_name and rule_code are required'}), 400
    
    try:
        rule = VerificationService.create_rule(
            rule_data=data,
            created_by_user_id=user_id
        )
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Created verification rule: {rule.rule_name}",
            resource_type='verification_rule',
            resource_id=str(rule.rule_id)
        )
        
        return jsonify({
            'message': 'Rule created successfully',
            'rule': VerificationService.rule_to_dict(rule)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@verification_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_rule(rule_id):
    """Update a verification rule"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    rule = VerificationService.update_rule(rule_id, data, updated_by_user_id=user_id)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Updated verification rule: {rule.rule_name}",
        resource_type='verification_rule',
        resource_id=str(rule.rule_id)
    )
    
    return jsonify({
        'message': 'Rule updated successfully',
        'rule': VerificationService.rule_to_dict(rule)
    }), 200


@verification_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_rule(rule_id):
    """Enable/disable a verification rule"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    is_active = data.get('is_active', True)
    
    rule = VerificationService.toggle_rule(rule_id, is_active)
    
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    action = 'enabled' if is_active else 'disabled'
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Verification rule {action}: {rule.rule_name}",
        resource_type='verification_rule',
        resource_id=str(rule.rule_id)
    )
    
    return jsonify({
        'message': f'Rule {action} successfully',
        'rule': VerificationService.rule_to_dict(rule)
    }), 200


@verification_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_rule(rule_id):
    """Delete a verification rule"""
    user_id = get_jwt_identity()
    
    success = VerificationService.delete_rule(rule_id)
    
    if not success:
        return jsonify({'error': 'Rule not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='delete',
        description=f"Deleted verification rule ID: {rule_id}",
        resource_type='verification_rule',
        resource_id=str(rule_id)
    )
    
    return jsonify({'message': 'Rule deleted successfully'}), 200


# ==================== VERIFICATION EXECUTION ====================
@verification_bp.route('/run/<report_id>', methods=['POST'])
@jwt_required()
def run_verification(report_id):
    """Run verification on a report"""
    user_id = get_jwt_identity()
    
    try:
        result = VerificationService.run_verification(report_id)
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='verify',
            description=f"Ran verification on report {report_id}",
            resource_type='report',
            resource_id=report_id
        )
        
        return jsonify({
            'message': 'Verification completed',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@verification_bp.route('/run-rule', methods=['POST'])
@jwt_required()
def run_single_rule():
    """Run a single verification rule on a report"""
    data = request.get_json()
    
    if not data.get('rule_id') or not data.get('report_id'):
        return jsonify({'error': 'rule_id and report_id are required'}), 400
    
    try:
        result = VerificationService.run_single_rule(
            rule_id=data['rule_id'],
            report_id=data['report_id']
        )
        
        return jsonify({
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXECUTION LOGS ====================
@verification_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_execution_logs():
    """Get rule execution logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('report_id'):
        filters['report_id'] = request.args.get('report_id')
    if request.args.get('rule_id'):
        filters['rule_id'] = request.args.get('rule_id', type=int)
    if request.args.get('passed'):
        filters['passed'] = request.args.get('passed').lower() == 'true'
    
    pagination = VerificationService.get_execution_logs(
        filters=filters, page=page, per_page=per_page
    )
    
    return jsonify({
        'logs': [VerificationService.execution_log_to_dict(l) for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@verification_bp.route('/logs/report/<report_id>', methods=['GET'])
@jwt_required()
def get_report_verification_logs(report_id):
    """Get verification logs for a specific report"""
    logs = VerificationService.get_report_execution_logs(report_id)
    
    return jsonify({
        'report_id': report_id,
        'logs': [VerificationService.execution_log_to_dict(l) for l in logs]
    }), 200


# ==================== STATISTICS ====================
@verification_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_verification_statistics():
    """Get verification statistics"""
    days = request.args.get('days', 30, type=int)
    
    stats = VerificationService.get_verification_statistics(days=days)
    
    return jsonify(stats), 200


@verification_bp.route('/rules/<int:rule_id>/statistics', methods=['GET'])
@jwt_required()
def get_rule_statistics(rule_id):
    """Get statistics for a specific rule"""
    days = request.args.get('days', 30, type=int)
    
    stats = VerificationService.get_rule_statistics(rule_id, days=days)
    
    if not stats:
        return jsonify({'error': 'Rule not found'}), 404
    
    return jsonify(stats), 200
