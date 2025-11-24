from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.models.user import User, UserRole, AuthProviderEnum

logger = logging.getLogger(__name__)

class UserCRUD:
    """Enhanced user CRUD operations with proper error handling"""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Get user by email with case-insensitive search
        """
        try:
            return db.query(User).filter(User.email.ilike(email)).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by email {email}: {e}")
            return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        """
        Get user by ID with validation
        """
        try:
            if not user_id or user_id <= 0:
                return None
            return db.query(User).filter(User.id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by ID {user_id}: {e}")
            return None

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password_hash: str = None,
        full_name: str = None,
        auth_provider: AuthProviderEnum = AuthProviderEnum.local,
        picture_url: str = None,
        role: UserRole = UserRole.investor
    ) -> User:
        """
        Create a new user with validation
        """
        try:
            # Validate email uniqueness
            existing_user = UserCRUD.get_user_by_email(db, email)
            if existing_user:
                raise ValueError(f"User with email {email} already exists")

            user = User(
                email=email.lower().strip(),
                hashed_password=password_hash,
                full_name=full_name,
                auth_provider=auth_provider,
                picture_url=picture_url,
                role=role,
                is_active=True
            )

            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User created successfully: {user.id} - {user.email}")
            return user

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating user {email}: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating user {email}: {e}")
            raise

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        update_data: dict
    ) -> User | None:
        """
        Update user information
        """
        try:
            user = UserCRUD.get_user_by_id(db, user_id)
            if not user:
                return None

            # Prevent updating protected fields
            protected_fields = {'id', 'created_at', 'email'}
            for field, value in update_data.items():
                if field in protected_fields:
                    continue
                if hasattr(user, field):
                    setattr(user, field, value)

            db.commit()
            db.refresh(user)
            return user

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating user {user_id}: {e}")
            return None

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """
        Deactivate user account
        """
        try:
            user = UserCRUD.get_user_by_id(db, user_id)
            if not user:
                return False

            user.is_active = False
            db.commit()
            logger.info(f"User deactivated: {user_id}")
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deactivating user {user_id}: {e}")
            return False

# Backward compatibility
def get_user_by_email(db: Session, email: str):
    return UserCRUD.get_user_by_email(db, email)

def get_user_by_id(db: Session, user_id: int):
    return UserCRUD.get_user_by_id(db, user_id)