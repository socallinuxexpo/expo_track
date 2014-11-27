from flask.ext.login import UserMixin
from werkzeug import generate_password_hash, check_password_hash

from ..app import db, login_manager
from ..utils import get_current_time

class User(db.Model, UserMixin):
    'A person who logs into the system and has certain privileges'

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    created_time = db.Column(db.DateTime, default=get_current_time, nullable=False)
    last_modified = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time, nullable=False)

    name = db.Column(db.String(32), unique=True, nullable=False)

    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    person = db.relationship('Person', backref=db.backref('user', lazy='dynamic'), uselist=False)

    # Password data and methods
    _password = db.Column('password', db.String(64), nullable=False)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, login, password):
        user = cls.query.filter(User.name == login).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    # Privileges
    can_edit_items = db.Column(db.Boolean)
    can_perform_action = db.Column(db.Boolean)
    can_edit_people = db.Column(db.Boolean)
    can_edit_events = db.Column(db.Boolean)
    can_edit_locations = db.Column(db.Boolean)
    can_edit_teams = db.Column(db.Boolean)

# Login Manager callbacks

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@login_manager.request_loader
def load_user_from_request(request):
    'Log in user using BasicAuth'

    auth = request.authorization
    # We need to ignore authentication headers for OPTIONS to avoid
    # unwanted interactions with CORS.
    # Chrome and Firefox issue a preflight OPTIONS request to check
    # Access-Control-* headers, and will fail if it returns 401.
    if request.method != 'OPTIONS':
        if auth:
            result = User.authenticate(auth.username, auth.password)
            # Return user object only if authenfication is successful
            if result[1]:
                return result[0]
    
    # finally, return None if BasicAuth did not work
    return None
