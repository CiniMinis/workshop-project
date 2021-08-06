from app import create_app
from app.config.avatar import Avatar


if __name__ == '__main__':
    app = create_app()
    # Sometimes to test /draw getting a dna sequence is nice
    print(Avatar.randomize().to_dna())
    app.run(host="0.0.0.0")
