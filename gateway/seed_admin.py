import os
import logging
from gateway.database import SessionLocal, init_db
from gateway.models.db import User
from gateway.auth import hash_password

logger = logging.getLogger("gateway.seed_admin")


def seed_admin_user():
    """
    Ensure at least one admin operator account exists in the database.
    Reads ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD from environment.
    """
    init_db()
    db = SessionLocal()
    try:
        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@consensus.dev")
        password = os.getenv("ADMIN_PASSWORD", "admin1234")

        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            logger.info(f"Admin operator already exists: {existing_user.username} ({existing_user.email})")
            return existing_user

        pwd_hash = hash_password(password)
        admin_user = User(
            username=username,
            email=email,
            password_hash=pwd_hash,
            role="admin",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"Successfully seeded admin operator: {username} ({email})")
        return admin_user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed admin user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_admin_user()
