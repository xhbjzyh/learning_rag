"""
通用工具方法
"""
def orm_to_dict(orm_obj):
    """
    SQLAlchemy ORM对象转可序列化JSON字典
    自动移除SQLAlchemy内部属性，处理datetime类型
    """
    if not orm_obj:
        return {}
    obj_dict = orm_obj.__dict__.copy()
    obj_dict.pop("_sa_instance_state", None)  # 移除SQLAlchemy内部状态
    # 处理datetime类型，转ISO标准字符串
    for k, v in obj_dict.items():
        if hasattr(v, "isoformat"):
            obj_dict[k] = v.isoformat()
    return obj_dict