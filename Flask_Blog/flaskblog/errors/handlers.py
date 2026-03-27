from flask import Blueprint, current_app, render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    current_app.logger.warning(f"404 error: {error}")
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(403)
def error_403(error):
    current_app.logger.warning(f"403 error: {error}")
    return render_template('errors/403.html'), 403


@errors.app_errorhandler(500)
def error_500(error):
    current_app.logger.warning(f"500 error: {error}")
    return render_template('errors/500.html'), 500


@errors.app_errorhandler(429)
def error_429(error):
    current_app.logger.warning(f"429 error: {error}")
    return render_template("errors/429.html"), 429