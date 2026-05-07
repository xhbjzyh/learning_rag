"""
用户-个人中心业务逻辑
"""
# 个人中心主要调用 auth_service 的 get_user_info 和 update_password
# 这里可以放一些个人中心特有的逻辑
from service.common.auth_service import auth_service


class PersonalCenterService:
    """个人中心服务类"""
    pass


personal_center_service = PersonalCenterService()