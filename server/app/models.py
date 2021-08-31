"""
    The application's models (MCV app setup).
    Configures database tables and configurations
"""
from sqlalchemy import literal
from app.config.avatar import Avatar
from app import db
from faker import Faker
from .modules.session_manager import SessionHandler
import random

def choose_with_prob(cand1, cand2, prob1):
    """Choose one of two options with given probability for cand1"""
    choice_weights = [prob1, 1 - prob1]
    return random.choices((cand1, cand2), choice_weights)[0]

class User(db.Model):
    """Database model for genetwork's users"""
    __tablename__ = 'users'
    # internal user id for database
    user_id = db.Column(db.Integer, primary_key=True)
    # dna sequence string
    dna = db.Column(db.Text, nullable=False)
    # are the avatar picture and dna sequence viewable
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    # cosmetic display data for profile
    name = db.Column(db.Text, nullable=False)
    job = db.Column(db.Text)
    location = db.Column(db.Text)

    def __str__(self):
        return f'<User {self.user_id}(name={self.name}, job={self.job},' +\
               f' location={self.location}, private={self.is_private})>'


class UserFactory:
    """Factory for creating random users
    
    Attributes:
        faker (Faker): a Faker instance for name generation.
            automatically created.
        avatar_cls (type): a sublass of AvatarBase (from avatar module)
            which represents the avatar of the generated users.
    """
    # constants for random user generation
    JOB_PROB = 0.75 # probability for the user showing a job
    LOCATION_PROB = 0.5 # probability for the user showing a location
    PRIVATE_PROB = 0.3  # probability for the user being private (hiding DNA)

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

    """dictionary which maps user properties to random generators for them"""
    randomizers = {
        'name': _name_randomizer,
        'job': _job_randomizer,
        'location': _location_randomizer,
        'is_private': _private_randomizer,
        'dna': _dna_randomizer
    }

    def randomize(self):
        """Create a random user

        Returns:
            User: a user with a randomized avatar and random faked parameters
        """
        random_vals = {key: rand(self) for key, rand in self.randomizers.items()}
        return User(**random_vals)


class Villain(db.Model):
    """Database model for the villains for each session"""
    __tablename__ = 'villains'

    _SESSION_HANDLER = SessionHandler()
    MAX_DETECTIONS = 5    # the maximal number of queries until the villain shapeshifts
    _EMERGENCY_OVER = 5

    # ssid of user to which the villain belongs
    ssid = db.Column(db.String(_SESSION_HANDLER.UUID_LEN), primary_key=True, nullable=False)
    # tracks the number queries to protected columns
    detections = db.Column(db.Integer, nullable=False, default=0)
    # dna for villain
    dna = db.Column(db.Text, nullable=False)

    # Properties which aren't real columns
    # These make the villain match the usual user columns
    FAKE_COLS = {
        'user_id': 666,
        'is_private': True,
        'name': "Raven Darkhölme",
        'location': "Earth-616",
        'job': None
    }

    _USER_FACTORY = UserFactory(Avatar)
    _DNA_RANDOMIZER = lambda: UserFactory.randomizers['dna'](Villain._USER_FACTORY)

    def shapeshift(self):
        """Changes the villains DNA and resets it's detections"""
        self.dna = Villain._DNA_RANDOMIZER()
        self.detections = 0
        db.session.commit()

    def notify_detection(self):
        """Update the session-villain's detection counter"""
        cur_detections = Villain.query.filter(Villain.ssid==self.ssid).first().detections
        self.detections = Villain.__table__.columns.detections + 1  # atomic inc
        db.session.commit()  # refresh data against db for accurate cur_detections
        if cur_detections == self.MAX_DETECTIONS or \
            self.detections > self.MAX_DETECTIONS + self._EMERGENCY_OVER:   # failsafe

            self.shapeshift()
    
    @staticmethod
    def is_villain(user):
        """Checks if the given user is a villain.

        This function works by checking all the faked user-columns
        and making sure each exists and all attributes are identical.
        If all the checks passed, the user is classified as a villain.

        Returns:
            bool: True if the user was classified a villain, false otherwise.
        """
        for col, fake_val in Villain.FAKE_COLS.items():
            if not hasattr(user, col):
                return False
            if getattr(user, col) != fake_val:
                return False
        return True

    @staticmethod
    def get_session_villain():
        """Returns the current session's villain"""
        cur_ssid = Villain._SESSION_HANDLER.ssid
        return Villain.query.filter_by(ssid=cur_ssid).first()

    @classmethod
    def get_user_columns(cls):
        """Generates fake columns to make villains match the User class"""
        user_col_names = [col.key for col in User.__table__.columns]
        fake_columns = []
        for col_name in user_col_names:
            if col_name in cls.FAKE_COLS:
                fake_columns.append(literal(cls.FAKE_COLS[col_name]).label(col_name))
            else:
                fake_columns.append(getattr(cls, col_name))
        return fake_columns

    @staticmethod
    @_SESSION_HANDLER.on_session_create
    def _make_villain(new_ssid):
        db.session.add(
            Villain(
                ssid=new_ssid,
                dna=Villain._DNA_RANDOMIZER(),
            )
        )
        db.session.commit()
    
    @staticmethod
    @_SESSION_HANDLER.on_session_delete
    def _delete_villain(ssid):
        Villain.query.filter_by(ssid=ssid).delete()
        db.session.commit()

class FakeQueryMeta(type):
    """Metaclass which allows a class to fake being a table!

    This metaclass given a query returning function, adds a fake static
    parameter with a custom query which fakes the SQLAlchemy QueryAPI.
    This can be used to create dynamic flask-sqlalchemy table lookalikes.
    """
    FAKE_QUERY_FUNC_NAME = "fake_query" # the name for the faked query method

    @property
    def query(cls):
        """QueryAPI faking for the database"""
        query_func = getattr(cls, cls.FAKE_QUERY_FUNC_NAME, None)
        if callable(query_func):
            return query_func()
        else:
            raise TypeError("query function not defined")


class SessionUsers(metaclass=FakeQueryMeta):
    """Table lookalike which holds all genetwork members for the session

    This is a faked flask-sqlalchemy table which dynamically adds the villain
    of the current session to the static filler-users in the genetwork page
    """
    _SESSION_HANDLER = SessionHandler()

    # References to the User columns
    # allows column access via this class instead of User
    name = User.name
    user_id = User.user_id
    dna = User.dna
    job = User.job
    location = User.location
    is_private = User.is_private

    @classmethod
    def fake_query(cls):
        """Generate the query for the fake QueryAPI"""
        static_users = User.query
        try:
            ssid = cls._SESSION_HANDLER.ssid
            relevant_villains = db.session.query(*Villain.get_user_columns()).filter(Villain.ssid==ssid)
            return relevant_villains.union(static_users)
        except ValueError:  # if no session exists, no villain exists.
            return static_users
