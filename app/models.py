from sqlalchemy import literal
from app.config.avatar import Avatar
from app import db
from faker import Faker
from .modules.ssid_manager import SessionIdManager
import random

def choose_with_prob(cand1, cand2, prob1):
    """
        Choose one of two options with given probability
    """
    choice_weights = [prob1, 1 - prob1]
    return random.choices((cand1, cand2), choice_weights)[0]

class User(db.Model):
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


class Villain(db.Model):
    __tablename__ = 'villains'

    _SSID_MANAGER = SessionIdManager()
    MAX_DETECTIONS = 2048
    _EMERGENCY_OVER = 5

    # ssid of user to which the villain belongs
    ssid = db.Column(db.String(_SSID_MANAGER.UUID_LEN), primary_key=True, nullable=False)
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
        self.dna = Villain._DNA_RANDOMIZER()
        self.detections = 0
        db.session.commit()

    def notify_detection(self):
        self.detections = Villain.__table__.columns.detections + 1  # atomic inc
        cur_detections = Villain.query.filter(Villain.ssid==self.ssid).first().detections
        db.session.commit()  # refresh data against db for accurate cur_detections
        if cur_detections == self.MAX_DETECTIONS or \
            self.detections > self.MAX_DETECTIONS + self._EMERGENCY_OVER:   # failsafe

            self.shapeshift()
    
    @staticmethod
    def is_villain(user):
        for col, fake_val in Villain.FAKE_COLS.items():
            if not hasattr(user, col):
                return False
            if getattr(user, col) != fake_val:
                return False
        return True

    @staticmethod
    def get_session_villain():
        cur_ssid = Villain._SSID_MANAGER.current_ssid
        return Villain.query.filter_by(ssid=cur_ssid).first()

    @classmethod
    def get_user_columns(cls):
        user_col_names = [col.key for col in User.__table__.columns]
        fake_columns = []
        for col_name in user_col_names:
            if col_name in cls.FAKE_COLS:
                fake_columns.append(literal(cls.FAKE_COLS[col_name]).label(col_name))
            else:
                fake_columns.append(getattr(cls, col_name))
        return fake_columns

    @staticmethod
    @SessionIdManager.call_on_new
    def _make_villain(new_ssid):
        db.session.add(
            Villain(
                ssid=new_ssid,
                dna=Villain._DNA_RANDOMIZER(),
            )
        )
        db.session.commit()

class FakeQueryMeta(type):
    FAKE_QUERY_FUNC_NAME = "fake_query"

    @property
    def query(cls):
        query_func = getattr(cls, cls.FAKE_QUERY_FUNC_NAME, None)
        if callable(query_func):
            return query_func()
        else:
            raise TypeError("query function not defined")


class SessionUsers(metaclass=FakeQueryMeta):
    _SSID_MANAGER = SessionIdManager()

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
        static_users = User.query
        try:
            ssid = cls._SSID_MANAGER.current_ssid
            relevant_villains = db.session.query(*Villain.get_user_columns()).filter(Villain.ssid==ssid)
            return relevant_villains.union(static_users)
        except ValueError:
            return static_users
