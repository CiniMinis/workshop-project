"""
    Runs the app.
    This is only for manual execution and must not be used in production!
"""

from app import create_app

DEPLOY_TYPE = 'prod'
CHALLENGE_TYPE = 'hard'

if __name__ == '__main__':
    app = create_app(deploy_type=DEPLOY_TYPE, challenge_type=CHALLENGE_TYPE)
    app.run(host="0.0.0.0")
