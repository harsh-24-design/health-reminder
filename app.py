import os
from flask import Flask, session
from config import Config
from database import init_db, close_db

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Register teardown
    app.teardown_appcontext(close_db)

    # Context processors for templates
    @app.context_processor
    def inject_global_vars():
        return {
            'logged_in': 'user_id' in session,
            'current_user_name': session.get('user_name', ''),
            'current_user_role': session.get('user_role', 'user'),
            'current_user_id': session.get('user_id', None)
        }

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.reminders import reminders_bp
    from routes.appointments import appointments_bp
    from routes.vitals import vitals_bp
    from routes.history import history_bp
    from routes.notifications import notifications_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(vitals_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    # Initialize SQLite database schema and seed data
    init_db(app)

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f" * Health Reminder Application running at http://127.0.0.1:{port}")
    print(" * Default Admin: admin@health.com / admin123")
    print(" * Sample User: john@example.com / john123")
    app.run(host='127.0.0.1', port=port, debug=True)
