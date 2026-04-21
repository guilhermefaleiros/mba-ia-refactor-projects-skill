from database import db
from utils.time import utcnow


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default="#000000")
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }

    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id.asc()).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def get_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_with_task_counts(cls):
        from models.task import Task

        counts = dict(
            db.session.query(Task.category_id, db.func.count(Task.id))
            .group_by(Task.category_id)
            .all()
        )
        return [
            {**category.to_dict(), "task_count": counts.get(category.id, 0)}
            for category in cls.list_all()
        ]
