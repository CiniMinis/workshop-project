from app import db
from faker import Faker
import random

def choose_with_prob(cand1, cand2, prob1):
    """
        Choose one of two options with given probability
    """
    choice_weights = [prob1, 1 - prob1]
    return random.choices((cand1, cand2), choice_weights)[0]

class User(db.Model):
    # internal user id for database
    user_id = db.Column(db.Integer, primary_key=True)
    # dna sequence string
    dna = db.Column(db.Text, nullable=False)
    # are the avatar picture and dna sequence viewable
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    # cosmetic display data for profile
    name = db.Column(db.Text, nullable=False, unique=True)
    job = db.Column(db.Text)
    location = db.Column(db.Text)

    def __str__(self):
        return f'<User {self.user_id}(name={self.name}, job={self.job},' +\
               f' location={self.location}, private={self.is_private})>'


class UserFactory:
    # constants for random user generation
    JOB_PROB = 0.75
    LOCATION_PROB = 0.5
    PRIVATE_PROB = 0.3

    def __init__(self, avatar_cls):
        self.faker = Faker()
        self.avatar_cls = avatar_cls

    # random generators for properties
    def _name_randomizer(self):
        return self.faker.unique.name()
    
    def _job_randomizer(self):
        return choose_with_prob(self.faker.job(), None, self.JOB_PROB)
    
    def _location_randomizer(self):
        _, _, place, country, _ = self.faker.location_on_land()
        return choose_with_prob(f"{place}, {country}", None, self.LOCATION_PROB)
    
    def _private_randomizer(self):
        return choose_with_prob(True, False, self.PRIVATE_PROB)

    def _dna_randomizer(self):
        return self.avatar_cls.randomize().to_dna()

    randomizers = {
        'name': _name_randomizer,
        'job': _job_randomizer,
        'location': _location_randomizer,
        'is_private': _private_randomizer,
        'dna': _dna_randomizer
    }

    def randomize(self):
        random_vals = {key: rand(self) for key, rand in self.randomizers.items()}
        return User(**random_vals)