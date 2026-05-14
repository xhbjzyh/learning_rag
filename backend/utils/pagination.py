"""
D:\projects\learning_rag\backend\utils\pagination.py
高效分页工具
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc


def cursor_pagination(
        db: Session,
        model,
        filters: list,
        order_by_field,
        limit: int = 20,
        cursor: str = None,
        reverse: bool = False
) -> Dict[str, Any]:
    """
    游标分页（比OFFSET快10-100倍）
    :param db: 数据库会话
    :param model: SQLAlchemy模型
    :param filters: 过滤条件列表
    :param order_by_field: 排序字段
    :param limit: 每页数量
    :param cursor: 上一页最后一条记录的ID
    :param reverse: 是否降序
    :return: 分页结果
    """
    query = db.query(model).filter(*filters)

    # 应用游标
    if cursor:
        if reverse:
            query = query.filter(order_by_field < cursor)
        else:
            query = query.filter(order_by_field > cursor)

    # 排序
    order_func = desc if reverse else lambda x: x
    query = query.order_by(order_func(order_by_field))

    # 取limit+1条（用于判断是否有下一页）
    items = query.limit(limit + 1).all()

    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    next_cursor = items[-1].id if items and has_next else None

    return {
        "items": items,
        "has_next": has_next,
        "next_cursor": next_cursor,
        "total": len(items)
    }
