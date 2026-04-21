from datetime import datetime
import re


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if not isinstance(email, str) or not email:
        return False
    return bool(re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", email))


def normalize_tags(tags):
    if not tags:
        return None
    if isinstance(tags, list):
        return ",".join(str(tag) for tag in tags)
    return tags


def parse_date(date_string):
    if not date_string:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except (TypeError, ValueError):
            continue
    raise ValueError("Data inválida")


def is_valid_color(color):
    return bool(color and len(color) == 7 and color.startswith("#"))
