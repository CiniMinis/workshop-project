from app import create_app
from app.config.avatar import Avatar


if __name__ == '__main__':
    app = create_app(deploy_type='dev', challenge_type='hard')
    # Sometimes to test /draw getting a dna sequence is nice
    print(Avatar.randomize().to_dna())
    app.run(host="0.0.0.0")
