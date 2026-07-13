"""SQLAlchemy database service."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DatabaseService:
    """Thin OOP wrapper around SQLAlchemy session operations."""

    def __init__(self, session=None):
        self._session = session or db.session

    @property
    def session(self):
        return self._session

    def add(self, instance):
        self._session.add(instance)
        return instance

    def delete(self, instance):
        self._session.delete(instance)
        return instance

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def flush(self):
        self._session.flush()

    def save(self, instance):
        """Add and commit a model instance."""
        self.add(instance)
        self.commit()
        return instance
