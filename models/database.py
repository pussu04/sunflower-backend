from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sunflower_analyses = db.relationship('SunflowerAnalysis', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the password with optimized method"""
        # Use pbkdf2:sha256 with lower iterations for faster hashing
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'age': self.age,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class SunflowerAnalysis(db.Model):
    __tablename__ = 'sunflower_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Analysis results
    predicted_class = db.Column(db.String(50), nullable=False)  # Disease class name
    confidence = db.Column(db.Float, nullable=False)
    all_predictions = db.Column(db.Text)  # JSON string of all class probabilities
    
    # Image processing info
    image_filename = db.Column(db.String(255))
    image_size = db.Column(db.String(50))  # e.g., "512x512"
    processing_time = db.Column(db.Float)  # in seconds
    
    # Cloudinary image URLs
    original_image_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert analysis object to dictionary"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'predicted_class': self.predicted_class,
            'confidence': self.confidence,
            'all_predictions': json.loads(self.all_predictions) if self.all_predictions else {},
            'image_info': {
                'filename': self.image_filename,
                'size': self.image_size,
                'processing_time': self.processing_time
            },
            'images': {
                'original_image_url': self.original_image_url
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<SunflowerAnalysis {self.id} - User {self.user_id} - {self.predicted_class}>'

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")