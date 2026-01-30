"""
ML Routes - Machine learning model management endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import MLService, AuditService

ml_routes_bp = Blueprint('ml_routes', __name__)


# ==================== MODEL MANAGEMENT ====================
@ml_routes_bp.route('/models', methods=['GET'])
@jwt_required()
def get_all_models():
    """Get all ML models"""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    models = MLService.get_all_models(include_inactive=include_inactive)
    
    return jsonify({
        'models': [MLService.model_to_dict(m) for m in models]
    }), 200


@ml_routes_bp.route('/models/active', methods=['GET'])
@jwt_required()
def get_active_model():
    """Get currently active model"""
    model = MLService.get_active_model()
    
    if not model:
        return jsonify({'error': 'No active model found'}), 404
    
    return jsonify({
        'model': MLService.model_to_dict(model)
    }), 200


@ml_routes_bp.route('/models/<model_id>', methods=['GET'])
@jwt_required()
def get_model(model_id):
    """Get model details"""
    model = MLService.get_model_by_id(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify({
        'model': MLService.model_to_dict(model)
    }), 200


@ml_routes_bp.route('/models', methods=['POST'])
@jwt_required()
def create_model():
    """Create a new ML model"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('model_name') or not data.get('model_type'):
        return jsonify({'error': 'model_name and model_type are required'}), 400
    
    try:
        model = MLService.create_model(data, created_by_user_id=user_id)
        
        AuditService.log_activity(
            user_id=user_id,
            activity_type='create',
            description=f"Created ML model: {model.model_name}",
            resource_type='ml_model',
            resource_id=model.model_id
        )
        
        return jsonify({
            'message': 'Model created successfully',
            'model': MLService.model_to_dict(model)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ml_routes_bp.route('/models/<model_id>/activate', methods=['POST'])
@jwt_required()
def activate_model(model_id):
    """Activate an ML model"""
    user_id = get_jwt_identity()
    
    model = MLService.activate_model(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Activated ML model: {model.model_name}",
        resource_type='ml_model',
        resource_id=model.model_id
    )
    
    return jsonify({
        'message': 'Model activated successfully',
        'model': MLService.model_to_dict(model)
    }), 200


@ml_routes_bp.route('/models/<model_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_model(model_id):
    """Deactivate an ML model"""
    user_id = get_jwt_identity()
    
    model = MLService.deactivate_model(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='update',
        description=f"Deactivated ML model: {model.model_name}",
        resource_type='ml_model',
        resource_id=model.model_id
    )
    
    return jsonify({
        'message': 'Model deactivated successfully',
        'model': MLService.model_to_dict(model)
    }), 200


# ==================== SCORING ====================
@ml_routes_bp.route('/score/<report_id>', methods=['POST'])
@jwt_required()
def score_report(report_id):
    """Calculate trust score for a report"""
    try:
        result = MLService.score_report(report_id)
        
        return jsonify({
            'message': 'Score calculated successfully',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ml_routes_bp.route('/score/batch', methods=['POST'])
@jwt_required()
def batch_score():
    """Score multiple reports"""
    data = request.get_json()
    
    if not data.get('report_ids'):
        return jsonify({'error': 'report_ids is required'}), 400
    
    results = []
    for report_id in data['report_ids']:
        try:
            result = MLService.score_report(report_id)
            results.append({'report_id': report_id, **result})
        except Exception as e:
            results.append({'report_id': report_id, 'error': str(e)})
    
    return jsonify({
        'message': 'Batch scoring completed',
        'results': results
    }), 200


# ==================== PREDICTIONS ====================
@ml_routes_bp.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    """Get prediction history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('report_id'):
        filters['report_id'] = request.args.get('report_id')
    if request.args.get('model_id'):
        filters['model_id'] = request.args.get('model_id')
    
    pagination = MLService.get_predictions(filters=filters, page=page, per_page=per_page)
    
    return jsonify({
        'predictions': [MLService.prediction_to_dict(p) for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@ml_routes_bp.route('/predictions/<report_id>', methods=['GET'])
@jwt_required()
def get_report_predictions(report_id):
    """Get predictions for a specific report"""
    predictions = MLService.get_report_predictions(report_id)
    
    return jsonify({
        'report_id': report_id,
        'predictions': [MLService.prediction_to_dict(p) for p in predictions]
    }), 200


@ml_routes_bp.route('/predictions/<prediction_id>/feedback', methods=['POST'])
@jwt_required()
def provide_feedback(prediction_id):
    """Provide feedback on a prediction"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if data.get('actual_outcome') is None:
        return jsonify({'error': 'actual_outcome is required'}), 400
    
    prediction = MLService.update_prediction_feedback(
        prediction_id=prediction_id,
        actual_outcome=data['actual_outcome'],
        feedback_by_user_id=user_id
    )
    
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404
    
    return jsonify({
        'message': 'Feedback recorded',
        'prediction': MLService.prediction_to_dict(prediction)
    }), 200


# ==================== TRAINING DATA ====================
@ml_routes_bp.route('/training-data', methods=['GET'])
@jwt_required()
def get_training_data():
    """Get training data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    is_validated = request.args.get('is_validated')
    
    if is_validated is not None:
        is_validated = is_validated.lower() == 'true'
    
    pagination = MLService.get_training_data(
        is_validated=is_validated,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'training_data': [MLService.training_data_to_dict(t) for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200


@ml_routes_bp.route('/training-data', methods=['POST'])
@jwt_required()
def add_training_data():
    """Add training data from a report"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('report_id') or data.get('label') is None:
        return jsonify({'error': 'report_id and label are required'}), 400
    
    try:
        training = MLService.add_training_data(
            report_id=data['report_id'],
            label=data['label'],
            validated_by_user_id=user_id
        )
        
        return jsonify({
            'message': 'Training data added',
            'training_data': MLService.training_data_to_dict(training)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@ml_routes_bp.route('/training-data/<training_id>/validate', methods=['POST'])
@jwt_required()
def validate_training_data(training_id):
    """Validate training data"""
    user_id = get_jwt_identity()
    
    training = MLService.validate_training_data(training_id, user_id)
    
    if not training:
        return jsonify({'error': 'Training data not found'}), 404
    
    return jsonify({
        'message': 'Training data validated',
        'training_data': MLService.training_data_to_dict(training)
    }), 200


# ==================== MODEL TRAINING ====================
@ml_routes_bp.route('/train', methods=['POST'])
@jwt_required()
def train_model():
    """Train a new model (placeholder for future implementation)"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    # This would trigger actual model training in a production environment
    # For now, return a placeholder response
    
    AuditService.log_activity(
        user_id=user_id,
        activity_type='create',
        description="Initiated model training",
        resource_type='ml_model'
    )
    
    return jsonify({
        'message': 'Model training initiated',
        'status': 'pending',
        'note': 'Training will run in background'
    }), 202


# ==================== STATISTICS ====================
@ml_routes_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_ml_statistics():
    """Get ML system statistics"""
    days = request.args.get('days', 30, type=int)
    
    stats = MLService.get_ml_statistics(days=days)
    
    return jsonify(stats), 200


@ml_routes_bp.route('/models/<model_id>/statistics', methods=['GET'])
@jwt_required()
def get_model_statistics(model_id):
    """Get statistics for a specific model"""
    days = request.args.get('days', 30, type=int)
    
    stats = MLService.get_model_statistics(model_id, days=days)
    
    if not stats:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify(stats), 200


@ml_routes_bp.route('/accuracy', methods=['GET'])
@jwt_required()
def get_model_accuracy():
    """Get model accuracy metrics"""
    model_id = request.args.get('model_id')
    days = request.args.get('days', 30, type=int)
    
    accuracy = MLService.calculate_model_accuracy(model_id=model_id, days=days)
    
    return jsonify(accuracy), 200
