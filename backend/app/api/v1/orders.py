from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.result import BaseResult
from app.models.user import User
from app.schemas.order import OrderCreate, OrderDetailOut, OrderItemOut, OrderOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("", response_model=BaseResult[OrderDetailOut])
async def create_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(
        None, alias="Idempotency-Key", max_length=64, description="客户端生成的结算标识，重试时复用"
    ),
):
    if idempotency_key:
        order_id = await order_service.find_order_for_retry(db, user.id, idempotency_key)
        if order_id is not None:
            return BaseResult.ok(await _detail(db, user.id, order_id), "订单已创建，返回已有订单")

    order = await order_service.create_order(db, user, data, idempotency_key=idempotency_key or None)
    detail = await _detail(db, user.id, order.id)
    # 订单、幂等键、库存与购物车一起提交。确认提交成功后再发成功响应。
    await db.commit()
    return BaseResult.ok(detail)


@router.get("", response_model=BaseResult[list[OrderOut]])
async def list_orders(
    status: int | None = Query(None, ge=1, le=7),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await order_service.list_orders(db, user.id, status=status, page=page, size=size)
    return BaseResult.ok([OrderOut.model_validate(r) for r in rows])


@router.get("/{order_id}", response_model=BaseResult[OrderDetailOut])
async def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order, items = await order_service.get_order_detail(db, user.id, order_id)
    return BaseResult.ok(_build_detail(order, items))


@router.post("/{order_id}/pay", response_model=BaseResult[OrderOut])
async def pay_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """模拟支付成功。真接支付渠道时这个入口换成异步回调 + 签名校验 + 幂等。"""
    order = await order_service.pay_order(db, user.id, order_id)
    return BaseResult.ok(OrderOut.model_validate(order))


@router.post("/{order_id}/cancel", response_model=BaseResult[OrderOut])
async def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.cancel_order(db, user.id, order_id)
    return BaseResult.ok(OrderOut.model_validate(order), "订单已取消")


@router.post("/{order_id}/confirm-receipt", response_model=BaseResult[OrderOut])
async def confirm_receipt(
    order_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = OrderOut.model_validate(await order_service.confirm_receipt(db, user.id, order_id))
    await db.commit()
    return BaseResult.ok(order)


async def _detail(db: AsyncSession, user_id: int, order_id: int) -> OrderDetailOut:
    # 走 get_order_detail 而不是自己 db.get：那个函数里带归属校验，
    # 在这里另起一条查询路径就等于绕过了越权检查
    order, items = await order_service.get_order_detail(db, user_id, order_id)
    return _build_detail(order, items)


def _build_detail(order, items) -> OrderDetailOut:
    detail = OrderDetailOut.model_validate(order)
    detail.items = [OrderItemOut.model_validate(i) for i in items]
    return detail
