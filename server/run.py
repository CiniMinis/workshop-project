"""
    Runs the app.
    This is only for manual execution and must not be used in production!
"""

from app import create_app

DEPLOY_TYPE = 'prod'
DIFFICULTY = 'hard'

if __name__ == '__main__':
    app = create_app(deploy_type=DEPLOY_TYPE, difficulty=DIFFICULTY)
    app.run(host="0.0.0.0")
