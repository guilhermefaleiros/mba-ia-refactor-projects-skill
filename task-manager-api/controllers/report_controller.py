from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError
from utils.constants import RECENT_ACTIVITY_DAYS
from utils.time import utcnow


def summary_report():
    total_tasks = Task.count_all()
    total_users = User.count_all()
    total_categories = Category.count_all()

    all_tasks = Task.list_all_with_relations()
    overdue_tasks = []
    tasks_by_user = {}
    completed_by_user = {}

    for task in all_tasks:
        tasks_by_user[task.user_id] = tasks_by_user.get(task.user_id, 0) + 1
        if task.status == "done":
            completed_by_user[task.user_id] = completed_by_user.get(task.user_id, 0) + 1
        if task.is_overdue():
            overdue_tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": (utcnow() - task.due_date).days,
                }
            )

    seven_days_ago = utcnow() - timedelta(days=RECENT_ACTIVITY_DAYS)
    user_stats = []
    for user in User.list_all():
        total = tasks_by_user.get(user.id, 0)
        completed = completed_by_user.get(user.id, 0)
        user_stats.append(
            {
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
            }
        )

    return {
        "generated_at": str(utcnow()),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": Task.counts_by_status(),
        "tasks_by_priority": Task.counts_by_priority_labels(),
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": overdue_tasks,
        },
        "recent_activity": {
            "tasks_created_last_7_days": Task.count_created_since(seven_days_ago),
            "tasks_completed_last_7_days": Task.count_completed_since(seven_days_ago),
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    tasks = Task.list_by_user(user_id)

    total = len(tasks)
    done = len([task for task in tasks if task.status == "done"])
    pending = len([task for task in tasks if task.status == "pending"])
    in_progress = len([task for task in tasks if task.status == "in_progress"])
    cancelled = len([task for task in tasks if task.status == "cancelled"])
    overdue = len([task for task in tasks if task.is_overdue()])
    high_priority = len([task for task in tasks if task.priority <= 2])

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        },
    }
