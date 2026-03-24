from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from flaskblog import db, login_manager
from flask_login import UserMixin

# Callback used by Flask-Login to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True) # Primary key for the user table
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg') # Profile image filename stored in the database
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False) # Whether the user has enabled two-factor authentication
    otp_secret = db.Column(db.String(32), nullable=True) # Secret key used to generate TOTP codes (Google Authenticator)

    # Generate a secure token for password reset
    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    # Verify a password reset token and return the associated user
    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id'] # Attempt to load token and extract user ID
        except:
            return None # Return None if token is invalid or expired
        return User.query.get(user_id)

    # String representation for debugging/loggin
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Primary key for posts
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(20), nullable=True) # Optional image file
    tags = db.Column(db.String(200), nullable=True, default="") # Optional tags users can include on their posts for search filters
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False, default="main")

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Primary key for comments
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author = db.relationship('User', backref='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key linking comment to its author
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) # Foreign key linking comment to its post