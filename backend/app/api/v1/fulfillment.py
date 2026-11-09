from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_fulfillment_staff
from app.core.database import get_db
from app.core.result import BaseResult
from app.schemas.common import Page
from app.schemas.order import OrderOut, OrderShipment
from app.services import order_service

router = APIRouter(
    prefix="/fulfillment/orders", tags=["订单履约"], dependencies=[Depends(require_fulfillment_staff)]
)


@router.get("", response_model=BaseResult[Page[OrderOut]])
async def pending_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await order_service.list_pending_shipments(db, page=page, size=size)
    return BaseResult.ok(Page(
        items=[OrderOut.model_validate(order) for order in orders], total=total, page=page, size=size
    ))


@router.post("/{order_id}/ship", response_model=BaseResult[OrderOut])
async def ship_order(order_id: int, shipment: OrderShipment, db: AsyncSession = Depends(get_db)):
    order = OrderOut.model_validate(await order_service.ship_order(db, order_id, shipment))
    await db.commit()
    return BaseResult.ok(order)
