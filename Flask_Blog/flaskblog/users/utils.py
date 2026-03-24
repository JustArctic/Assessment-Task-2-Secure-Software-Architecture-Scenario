import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from flaskblog import mail

# Save a user's uploaded profile picture
def save_picture(form_picture):
    random_hex = secrets.token_hex(8) # Generate a random hex string to avoid filename collisions
    _, f_ext = os.path.splitext(form_picture.filename) # Extract the file extension from the uploaded file
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn # Return the filename so it can be stored in the database

# Send a password reset email to the user
def send_reset_email(user):
    token = user.get_reset_token() # Generate a secure token for password reset
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    # Email body includes a link to the reset page with the token
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg) # Send the email using Flask-Mail
