from database import db
from utils.security import hash_password, verify_password
from utils.time import utcnow


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, plain_password, rounds=12):
        self.password = hash_password(plain_password, rounds=rounds)

    def check_password(self, plain_password):
        return verify_password(plain_password, self.password)

    def is_admin(self):
        return self.role == "admin"

    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id.asc()).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list_with_task_counts(cls):
        from models.task import Task

        counts = dict(
            db.session.query(Task.user_id, db.func.count(Task.id))
            .group_by(Task.user_id)
            .all()
        )
        users = cls.list_all()
        return [
            {
                **user.to_dict(),
                "task_count": counts.get(user.id, 0),
            }
            for user in users
        ]
