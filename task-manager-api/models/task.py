from database import db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from utils.constants import VALID_TASK_STATUSES
from utils.time import utcnow


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tags.split(",") if self.tags else [],
        }

    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status in {"done", "cancelled"}:
            return False
        return self.due_date < utcnow()

    @classmethod
    def list_all(cls):
        return cls.query.order_by(cls.id.asc()).all()

    @classmethod
    def list_all_with_relations(cls):
        return cls.query.options(
            joinedload(cls.user),
            joinedload(cls.category),
        ).order_by(cls.id.asc()).all()

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def get_by_id_with_relations(cls, task_id):
        return (
            cls.query.options(joinedload(cls.user), joinedload(cls.category))
            .filter_by(id=task_id)
            .first()
        )

    @classmethod
    def list_by_user(cls, user_id):
        return (
            cls.query.options(joinedload(cls.user), joinedload(cls.category))
            .filter_by(user_id=user_id)
            .order_by(cls.id.asc())
            .all()
        )

    @classmethod
    def list_by_category(cls, category_id):
        return cls.query.filter_by(category_id=category_id).order_by(cls.id.asc()).all()

    @classmethod
    def search(cls, query="", status="", priority=None, user_id=None):
        query_obj = cls.query.options(joinedload(cls.user), joinedload(cls.category))
        if query:
            term = f"%{query}%"
            query_obj = query_obj.filter(
                or_(
                    cls.title.ilike(term),
                    cls.description.ilike(term),
                )
            )
        if status:
            query_obj = query_obj.filter(cls.status == status)
        if priority not in (None, ""):
            query_obj = query_obj.filter(cls.priority == int(priority))
        if user_id not in (None, ""):
            query_obj = query_obj.filter(cls.user_id == int(user_id))
        return query_obj.order_by(cls.id.asc()).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def count_by_status(cls, status):
        return cls.query.filter_by(status=status).count()

    @classmethod
    def counts_by_status(cls):
        return {
            status: cls.count_by_status(status)
            for status in VALID_TASK_STATUSES
        }

    @classmethod
    def counts_by_priority_labels(cls):
        return {
            "critical": cls.query.filter_by(priority=1).count(),
            "high": cls.query.filter_by(priority=2).count(),
            "medium": cls.query.filter_by(priority=3).count(),
            "low": cls.query.filter_by(priority=4).count(),
            "minimal": cls.query.filter_by(priority=5).count(),
        }

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_completed_since(cls, since):
        return cls.query.filter(cls.status == "done", cls.updated_at >= since).count()

    @classmethod
    def count_overdue(cls):
        return len([task for task in cls.list_all_with_relations() if task.is_overdue()])
