"""
用户-用户画像业务逻辑
"""
from sqlalchemy.orm import Session

from models.db_models import UserProfile
from utils.logger import logger


class UserProfileService:
    """用户画像服务类"""

    @staticmethod
    def get_user_profile(user_id: int, db: Session):
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id, tag_weight="{}")
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile


user_profile_service = UserProfileService()