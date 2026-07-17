from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permissions
from app.modules.auth.service import user_permissions
from app.modules.inventory.models import InventoryBatch, InventoryTransaction
from app.modules.inventory.schemas import (
    InventoryAdjustmentCreate,
    InventoryBatchCreate,
    InventoryBatchRead,
    InventoryBatchUpdate,
    InventorySummary,
    InventoryTransactionRead,
)
from app.modules.inventory.service import (
    adjust_inventory,
    available_batches,
    create_batch,
    get_batch,
    inventory_summary,
    list_batches,
    list_transactions,
    update_batch,
)
from app.modules.users.models import User

router = APIRouter(tags=["inventory"])


def require_inventory_reader(current_user: User = Depends(get_current_user)) -> User:
    granted = set(user_permissions(current_user))
    if not ({"inventory:manage", "pharmacy:dispense"} & granted):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return current_user


@router.get("/inventory", response_model=list[InventoryBatchRead])
def get_inventory(
    search: str = "",
    active_only: bool = False,
    available_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_inventory_reader),
) -> list[InventoryBatch]:
    return list_batches(db, search=search, active_only=active_only, available_only=available_only)


@router.get("/inventory/summary", response_model=InventorySummary)
def get_inventory_summary(
    db: Session = Depends(get_db),
    _=Depends(require_inventory_reader),
) -> InventorySummary:
    return inventory_summary(db)


@router.post("/inventory/batches", response_model=InventoryBatchRead, status_code=201)
def post_inventory_batch(
    payload: InventoryBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> InventoryBatch:
    return create_batch(db, payload, current_user)


@router.get("/inventory/batches/{batch_id}", response_model=InventoryBatchRead)
def get_inventory_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_inventory_reader),
) -> InventoryBatch:
    return get_batch(db, batch_id)


@router.patch("/inventory/batches/{batch_id}", response_model=InventoryBatchRead)
def patch_inventory_batch(
    batch_id: UUID,
    payload: InventoryBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> InventoryBatch:
    return update_batch(db, batch_id, payload, current_user)


@router.post("/inventory/adjustments", response_model=InventoryBatchRead)
def post_inventory_adjustment(
    payload: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> InventoryBatch:
    return adjust_inventory(db, payload, current_user)


@router.get("/inventory/transactions", response_model=list[InventoryTransactionRead])
def get_inventory_transactions(
    medication_id: UUID | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_inventory_reader),
) -> list[InventoryTransaction]:
    return list_transactions(db, medication_id)


@router.get("/medications/{medication_id}/available-batches", response_model=list[InventoryBatchRead])
def get_available_batches(
    medication_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_inventory_reader),
) -> list[InventoryBatch]:
    return available_batches(db, medication_id)
