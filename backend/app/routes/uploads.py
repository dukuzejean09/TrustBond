"""
File upload endpoints for evidence and attachments.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

uploads_bp = Blueprint('uploads', __name__)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

ALL_ALLOWED_EXTENSIONS = (
    ALLOWED_IMAGE_EXTENSIONS | 
    ALLOWED_VIDEO_EXTENSIONS | 
    ALLOWED_AUDIO_EXTENSIONS | 
    ALLOWED_DOCUMENT_EXTENSIONS
)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALL_ALLOWED_EXTENSIONS


def get_file_type(filename):
    """Get file type category"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return 'document'
    return 'unknown'


@uploads_bp.route('/evidence', methods=['POST'])
def upload_evidence():
    """Upload evidence file for a report"""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': 'File type not allowed',
            'allowedTypes': list(ALL_ALLOWED_EXTENSIONS)
        }), 400
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    
    # Create upload directory if it doesn't exist
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'evidence')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Get file info
    file_size = os.path.getsize(file_path)
    file_type = get_file_type(original_filename)
    
    # Generate URL (in production, this would be a CDN or cloud storage URL)
    file_url = f"/api/uploads/evidence/{unique_filename}"
    
    return jsonify({
        'success': True,
        'file': {
            'url': file_url,
            'filename': unique_filename,
            'originalFilename': original_filename,
            'type': file_type,
            'size': file_size,
            'uploadedAt': datetime.utcnow().isoformat()
        }
    }), 201


@uploads_bp.route('/evidence/<filename>', methods=['GET'])
def get_evidence(filename):
    """Serve an uploaded evidence file"""
    from flask import send_from_directory
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'evidence')
    return send_from_directory(upload_folder, filename)


@uploads_bp.route('/evidence/multiple', methods=['POST'])
def upload_multiple_evidence():
    """Upload multiple evidence files"""
    if 'files' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No files provided'
        }), 400
    
    files = request.files.getlist('files')
    
    if len(files) == 0:
        return jsonify({
            'success': False,
            'error': 'No files selected'
        }), 400
    
    if len(files) > 10:
        return jsonify({
            'success': False,
            'error': 'Maximum 10 files allowed per upload'
        }), 400
    
    uploaded_files = []
    errors = []
    
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'evidence')
    os.makedirs(upload_folder, exist_ok=True)
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            errors.append({
                'filename': file.filename,
                'error': 'File type not allowed'
            })
            continue
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        
        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_type = get_file_type(original_filename)
        file_url = f"/api/uploads/evidence/{unique_filename}"
        
        uploaded_files.append({
            'url': file_url,
            'filename': unique_filename,
            'originalFilename': original_filename,
            'type': file_type,
            'size': file_size,
            'uploadedAt': datetime.utcnow().isoformat()
        })
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'errors': errors if errors else None,
        'totalUploaded': len(uploaded_files)
    }), 201


@uploads_bp.route('/evidence/<filename>', methods=['DELETE'])
def delete_evidence(filename):
    """Delete an uploaded evidence file"""
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'evidence')
    file_path = os.path.join(upload_folder, secure_filename(filename))
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'File not found'
        }), 404
