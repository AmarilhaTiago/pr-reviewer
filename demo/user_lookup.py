import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    query = f"SELECT id, email FROM users WHERE name = '{name}'"
    return conn.execute(query).fetchall()


def average_score(scores: list[float]) -> float:
    return sum(scores) / len(scores)


def add_tag(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags


def normalize(name: str) -> str:
    return name.strip().lower()
