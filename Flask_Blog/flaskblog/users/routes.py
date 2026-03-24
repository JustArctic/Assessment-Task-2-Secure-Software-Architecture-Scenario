from flask import current_app, render_template, url_for, flash, redirect, request, Blueprint, session
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog import db, bcrypt, limiter
from flaskblog.models import User, Post
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm,
                                   Enable2FAForm, Verify2FAForm)
from flaskblog.users.utils import save_picture, send_reset_email
from flaskblog.utils import is_safe_url
import pyotp, qrcode, os

# Blueprint for all user-related routes (authentication, profiles, account management)
users = Blueprint('users', __name__)

# ---------------------------------------------------------
# Registration method
# ---------------------------------------------------------
@users.route("/register", methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    # Redirect authenticated users away from the registration page
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    # Handle form submission
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data) # Hash the user's password before storing it
        user = User(username=form.username.data, email=form.email.data, password=hashed_password) # Create new user instance
        # Save user to database
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        next_page = request.args.get('next')
        # Test if redirect is valid
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)

# ---------------------------------------------------------
# Login method
# ---------------------------------------------------------
@users.route("/login", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # Redirect authenticated users away from login page
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() # Look up user by email
        # Validate password
        if user and bcrypt.check_password_hash(user.password, form.password.data):

            # If user has 2FA enabled → redirect to verification step
            if user.two_factor_enabled:
                session['2fa_user_id'] = user.id
                session['remember_me'] = form.remember.data
                return redirect(url_for('users.verify_2fa'))

            login_user(user, remember=form.remember.data) # Log the user in, optionally remembering their session
            
            # Redirect to the page the user originally wanted to access
            next_page = request.args.get('next')
            # Test if redirect is valid
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

# Log the user out and redirect to home
@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# ---------------------------------------------------------
# Access account page
# ---------------------------------------------------------
@users.route("/account", methods=['GET', 'POST'])
@login_required # Only logged-in users can access their account page
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # If a new profile picture was uploaded, save it
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data # Update username
        current_user.email = form.email.data # Update email
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account')) # Redirect to avoid form resubmission issues
    elif request.method == 'GET':
        # Pre-fill form fields with current user data
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

# ---------------------------------------------------------
# Pagination
# ---------------------------------------------------------
@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int) # Pagination for user-specific posts
    user = User.query.filter_by(username=username).first_or_404() # Fetch user or return 404
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

# ---------------------------------------------------------
# Password reset e-mail protection
# ---------------------------------------------------------
@users.route("/reset_password", methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def reset_request():
    if current_user.is_authenticated: # Prevent logged-in users from requesting password resets
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() # Look up user by email
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form) # Render password reset request form

# ---------------------------------------------------------
# Generate new token when user resets password
# ---------------------------------------------------------
@users.route("/reset_password/<token>", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def reset_token(token):
    if current_user.is_authenticated: # Prevent logged-in users from resetting passwords
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token) # Validate token and retrieve user
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data) # Hash new password
        user.password = hashed_password # Update user's password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# ---------------------------------------------------------
# ENABLE 2FA — user scans QR code and confirms setup
# ---------------------------------------------------------
@users.route("/enable_2fa", methods=['GET', 'POST'])
@login_required
def enable_2fa():
    form = Enable2FAForm()
    # Generate secret if user doesn't have one yet
    if not current_user.otp_secret:
        current_user.otp_secret = pyotp.random_base32()
        db.session.commit()
    # Generate provisioning URI for Google Authenticator
    totp = pyotp.TOTP(current_user.otp_secret)
    qr_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="FlaskBlog"
    )
    if form.validate_on_submit():
        if totp.verify(form.code.data):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash("Two-factor authentication enabled!", "success")
            return redirect(url_for('users.account'))
        else:
            flash("Invalid authentication code. Try again.", "danger")
        return render_template("enable_2fa.html", form=form, qr_uri=qr_uri)
    # Generate QR code image
    qr_img = qrcode.make(qr_uri)
    qr_folder = os.path.join(current_app.root_path, 'static/qr_codes')
    os.makedirs(qr_folder, exist_ok=True)

    qr_path = os.path.join(qr_folder, f"{current_user.id}.png")
    qr_img.save(qr_path)

    qr_image_url = url_for('static', filename=f"qr_codes/{current_user.id}.png")
    # Handle form submission
    if form.validate_on_submit():
        if totp.verify(form.code.data):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash("Two-factor authentication enabled!", "success")
            return redirect(url_for('users.account'))
        else:
            flash("Invalid authentication code. Try again.", "danger")
    return render_template("enable_2fa.html", form=form, qr_image_url=qr_image_url)

# ---------------------------------------------------------
# VERIFY 2FA — second step of login
# ---------------------------------------------------------
@users.route("/verify_2fa", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('users.login'))
    form = Verify2FAForm()
    user = User.query.get(session['2fa_user_id'])
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(form.code.data):
            login_user(user, remember=session.get('remember_me', False))
            # Cleanup session
            session.pop('2fa_user_id', None)
            session.pop('remember_me', None)
            return redirect(url_for('main.home'))
        else:
            flash("Invalid authentication code.", "danger")
    return render_template("verify_2fa.html", form=form)

# ---------------------------------------------------------
# Disable 2FA (optional)
# ---------------------------------------------------------
@users.route("/disable_2fa", methods=['POST'])
@login_required
def disable_2fa():
    current_user.two_factor_enabled = False
    current_user.otp_secret = None
    db.session.commit()
    flash("Two-factor authentication has been disabled.", "danger")
    return redirect(url_for('users.account'))
