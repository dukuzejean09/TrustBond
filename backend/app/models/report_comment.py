"""
Report Comment Model for Case Updates and Communication.

Allows officers to add updates/notes to reports and enables
communication through a report's lifecycle.
"""

from app import db
from datetime import datetime
import enum


class CommentType(enum.Enum):
    """Types of comments on reports."""
    UPDATE = 'update'           # Status update
    NOTE = 'note'               # Internal note (officers only)
    EVIDENCE = 'evidence'       # New evidence added
    ASSIGNMENT = 'assignment'   # Assignment change
    RESOLUTION = 'resolution'   # Resolution notes
    QUERY = 'query'            # Question/clarification needed
    RESPONSE = 'response'       # Response to query


class CommentVisibility(enum.Enum):
    """Visibility levels for comments."""
    INTERNAL = 'internal'       # Officers/admins only
    REPORTER = 'reporter'       # Visible to reporter too
    PUBLIC = 'public'           # Visible in public tracking


class ReportComment(db.Model):
    """
    Stores comments and updates on reports.
    """
    __tablename__ = 'report_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to report
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False, index=True)
    
    # Author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    author_name = db.Column(db.String(100))  # Denormalized for display
    author_role = db.Column(db.String(20))
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.Enum(CommentType), default=CommentType.NOTE)
    visibility = db.Column(db.Enum(CommentVisibility), default=CommentVisibility.INTERNAL)
    
    # Attachments
    attachments = db.Column(db.JSON, default=list)
    
    # For threaded replies
    parent_id = db.Column(db.Integer, db.ForeignKey('report_comments.id'))
    
    # Status tracking (for status-change comments)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    
    # Relationships
    report = db.relationship('Report', backref=db.backref('comments', lazy='dynamic', order_by='ReportComment.created_at'))
    author = db.relationship('User', backref='report_comments')
    replies = db.relationship('ReportComment', backref=db.backref('parent', remote_side=[id]))
    
    def to_dict(self, include_replies=True):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'reportId': self.report_id,
            'authorId': self.author_id,
            'authorName': self.author_name,
            'authorRole': self.author_role,
            'content': self.content,
            'type': self.comment_type.value,
            'visibility': self.visibility.value,
            'attachments': self.attachments,
            'parentId': self.parent_id,
            'oldStatus': self.old_status,
            'newStatus': self.new_status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'isEdited': self.is_edited
        }
        
        if include_replies and self.replies:
            data['replies'] = [reply.to_dict(include_replies=False) for reply in self.replies]
        
        return data
    
    def __repr__(self):
        return f'<ReportComment {self.id} on Report {self.report_id}>'


def add_comment(report, user, content, comment_type=CommentType.NOTE, 
                visibility=CommentVisibility.INTERNAL, attachments=None,
                old_status=None, new_status=None):
    """
    Helper function to add a comment to a report.
    
    Args:
        report: Report object
        user: User adding the comment (can be None for system comments)
        content: Comment text
        comment_type: Type of comment
        visibility: Who can see this comment
        attachments: List of attachment URLs
        old_status: Previous status (for status change comments)
        new_status: New status (for status change comments)
    
    Returns:
        ReportComment object
    """
    comment = ReportComment(
        report_id=report.id,
        author_id=user.id if user else None,
        author_name=f"{user.first_name} {user.last_name}" if user else "System",
        author_role=user.role.value if user and user.role else "system",
        content=content,
        comment_type=comment_type,
        visibility=visibility,
        attachments=attachments or [],
        old_status=old_status,
        new_status=new_status
    )
    db.session.add(comment)
    return comment


def add_status_change_comment(report, user, old_status, new_status, note=None):
    """Add a comment recording status change."""
    content = f"Status changed from {old_status} to {new_status}"
    if note:
        content += f": {note}"
    
    return add_comment(
        report=report,
        user=user,
        content=content,
        comment_type=CommentType.UPDATE,
        visibility=CommentVisibility.REPORTER,
        old_status=old_status,
        new_status=new_status
    )


def add_assignment_comment(report, user, officer):
    """Add a comment recording assignment."""
    return add_comment(
        report=report,
        user=user,
        content=f"Case assigned to {officer.first_name} {officer.last_name} ({officer.badge_number or 'No badge'})",
        comment_type=CommentType.ASSIGNMENT,
        visibility=CommentVisibility.INTERNAL
    )


def add_resolution_comment(report, user, resolution_notes):
    """Add a comment for case resolution."""
    return add_comment(
        report=report,
        user=user,
        content=resolution_notes,
        comment_type=CommentType.RESOLUTION,
        visibility=CommentVisibility.REPORTER
    )
