from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.audit_logs.service import write_audit_log
from app.modules.dispensing.models import DispensingItem
from app.modules.inventory.models import InventoryBatch, InventoryTransaction, InventoryTransactionType
from app.modules.inventory.schemas import InventoryAdjustmentCreate, InventoryBatchCreate, InventoryBatchUpdate, InventorySummary
from app.modules.medications.models import Medication
from app.modules.prescriptions.models import PrescriptionItem
from app.modules.users.models import User

LOW_STOCK_THRESHOLD = Decimal("10.00")
EXPIRY_WARNING_DAYS = 30


def get_batch(db: Session, batch_id: UUID) -> InventoryBatch:
    batch = db.execute(
        select(InventoryBatch)
        .where(InventoryBatch.id == batch_id)
        .options(selectinload(InventoryBatch.medication))
    ).scalar_one_or_none()
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory batch not found")
    return batch


def write_inventory_transaction(
    db: Session,
    batch: InventoryBatch,
    *,
    transaction_type: InventoryTransactionType,
    quantity: Decimal,
    quantity_before: Decimal,
    quantity_after: Decimal,
    reserved_before: Decimal,
    reserved_after: Decimal,
    reference_type: str = "",
    reference_id: UUID | None = None,
    reason: str = "",
    actor: User | None = None,
    idempotency_key: str | None = None,
) -> InventoryTransaction:
    transaction = InventoryTransaction(
        medication_id=batch.medication_id,
        inventory_batch_id=batch.id,
        transaction_type=transaction_type,
        quantity=quantity,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reserved_before=reserved_before,
        reserved_after=reserved_after,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
        performed_by=actor.id if actor else None,
        idempotency_key=idempotency_key,
        created_at=datetime.now(timezone.utc),
    )
    db.add(transaction)
    return transaction


def create_batch(db: Session, payload: InventoryBatchCreate, actor: User) -> InventoryBatch:
    medication = db.get(Medication, payload.medication_id)
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    if payload.expiry_date < date.today():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot receive an expired batch")
    batch = InventoryBatch(
        medication_id=payload.medication_id,
        batch_number=payload.batch_number,
        expiry_date=payload.expiry_date,
        quantity_on_hand=payload.quantity,
        reserved_quantity=Decimal("0.00"),
        unit=payload.unit,
        location=payload.location,
        received_at=payload.received_at or datetime.now(timezone.utc),
        is_active=True,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(batch)
    db.flush()
    write_inventory_transaction(
        db,
        batch,
        transaction_type=InventoryTransactionType.RECEIVE,
        quantity=payload.quantity,
        quantity_before=Decimal("0.00"),
        quantity_after=payload.quantity,
        reserved_before=Decimal("0.00"),
        reserved_after=Decimal("0.00"),
        reference_type="inventory_batch",
        reference_id=batch.id,
        reason="Receive inventory batch",
        actor=actor,
    )
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="INVENTORY_BATCH_CREATED",
        entity_type="inventory_batch",
        entity_id=batch.id,
        summary=f"Received {payload.quantity} {payload.unit} for medication {medication.code}",
    )
    db.commit()
    return get_batch(db, batch.id)


def update_batch(db: Session, batch_id: UUID, payload: InventoryBatchUpdate, actor: User) -> InventoryBatch:
    batch = get_batch(db, batch_id)
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(batch, key, value)
    batch.updated_by = actor.id
    batch.version += 1
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="INVENTORY_BATCH_UPDATED",
        entity_type="inventory_batch",
        entity_id=batch.id,
        summary=f"Updated inventory batch {batch.batch_number}",
    )
    db.commit()
    return get_batch(db, batch.id)


def list_batches(
    db: Session,
    *,
    search: str = "",
    medication_id: UUID | None = None,
    active_only: bool = False,
    available_only: bool = False,
) -> list[InventoryBatch]:
    statement = select(InventoryBatch).options(selectinload(InventoryBatch.medication)).order_by(
        InventoryBatch.expiry_date.asc(), InventoryBatch.received_at.asc()
    )
    if medication_id:
        statement = statement.where(InventoryBatch.medication_id == medication_id)
    if active_only:
        statement = statement.where(InventoryBatch.is_active.is_(True))
    if available_only:
        statement = statement.where(InventoryBatch.quantity_on_hand > InventoryBatch.reserved_quantity)
    if search:
        keyword = f"%{search.strip()}%"
        statement = statement.join(Medication, Medication.id == InventoryBatch.medication_id).where(
            or_(Medication.name.ilike(keyword), Medication.code.ilike(keyword), InventoryBatch.batch_number.ilike(keyword))
        )
    return list(db.execute(statement.limit(300)).scalars())


def available_batches(db: Session, medication_id: UUID) -> list[InventoryBatch]:
    today = date.today()
    statement = (
        select(InventoryBatch)
        .where(
            InventoryBatch.medication_id == medication_id,
            InventoryBatch.is_active.is_(True),
            InventoryBatch.expiry_date >= today,
            InventoryBatch.quantity_on_hand > InventoryBatch.reserved_quantity,
        )
        .options(selectinload(InventoryBatch.medication))
        .order_by(InventoryBatch.expiry_date.asc(), InventoryBatch.received_at.asc())
    )
    return list(db.execute(statement.limit(100)).scalars())


def inventory_summary(db: Session) -> InventorySummary:
    batches = list(db.execute(select(InventoryBatch)).scalars())
    today = date.today()
    expiry_limit = today + timedelta(days=EXPIRY_WARNING_DAYS)
    total_on_hand = sum((batch.quantity_on_hand for batch in batches), Decimal("0.00"))
    total_reserved = sum((batch.reserved_quantity for batch in batches), Decimal("0.00"))
    return InventorySummary(
        batch_count=len(batches),
        active_batch_count=sum(1 for batch in batches if batch.is_active),
        total_on_hand=total_on_hand,
        total_reserved=total_reserved,
        total_available=total_on_hand - total_reserved,
        low_stock_count=sum(1 for batch in batches if batch.quantity_on_hand - batch.reserved_quantity <= LOW_STOCK_THRESHOLD),
        expiring_count=sum(1 for batch in batches if today <= batch.expiry_date <= expiry_limit),
        expired_count=sum(1 for batch in batches if batch.expiry_date < today),
    )


def adjust_inventory(db: Session, payload: InventoryAdjustmentCreate, actor: User) -> InventoryBatch:
    batch = get_batch(db, payload.batch_id)
    allowed = {
        InventoryTransactionType.ADJUST_INCREASE,
        InventoryTransactionType.ADJUST_DECREASE,
        InventoryTransactionType.EXPIRE,
        InventoryTransactionType.DISCARD,
    }
    if payload.adjustment_type not in allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unsupported inventory adjustment type")
    quantity_before = batch.quantity_on_hand
    reserved_before = batch.reserved_quantity
    if payload.adjustment_type == InventoryTransactionType.ADJUST_INCREASE:
        batch.quantity_on_hand += payload.quantity
    elif payload.adjustment_type in {
        InventoryTransactionType.ADJUST_DECREASE,
        InventoryTransactionType.DISCARD,
    }:
        next_quantity = batch.quantity_on_hand - payload.quantity
        if next_quantity < batch.reserved_quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Adjustment would reduce stock below reserved quantity")
        batch.quantity_on_hand = next_quantity
    elif payload.adjustment_type == InventoryTransactionType.EXPIRE:
        if batch.reserved_quantity > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reserved batch cannot be expired")
        batch.is_active = False
    batch.updated_by = actor.id
    batch.version += 1
    write_inventory_transaction(
        db,
        batch,
        transaction_type=payload.adjustment_type,
        quantity=payload.quantity,
        quantity_before=quantity_before,
        quantity_after=batch.quantity_on_hand,
        reserved_before=reserved_before,
        reserved_after=batch.reserved_quantity,
        reference_type="inventory_adjustment",
        reference_id=batch.id,
        reason=payload.reason,
        actor=actor,
    )
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="INVENTORY_ADJUSTED",
        entity_type="inventory_batch",
        entity_id=batch.id,
        summary=f"{payload.adjustment_type.value}: {payload.reason}",
    )
    db.commit()
    return get_batch(db, batch.id)


def list_transactions(db: Session, medication_id: UUID | None = None) -> list[InventoryTransaction]:
    statement = select(InventoryTransaction).order_by(InventoryTransaction.created_at.desc())
    if medication_id:
        statement = statement.where(InventoryTransaction.medication_id == medication_id)
    return list(db.execute(statement.limit(300)).scalars())


def reserve_prescription_items(
    db: Session,
    *,
    dispensing_record_id: UUID,
    prescription_items: list[PrescriptionItem],
    actor: User,
) -> list[DispensingItem]:
    allocations: list[tuple[PrescriptionItem, InventoryBatch, Decimal]] = []
    today = date.today()
    for item in prescription_items:
        required = item.quantity
        candidates = db.execute(
            select(InventoryBatch)
            .where(
                InventoryBatch.medication_id == item.medication_id,
                InventoryBatch.is_active.is_(True),
                InventoryBatch.expiry_date >= today,
                InventoryBatch.quantity_on_hand > InventoryBatch.reserved_quantity,
            )
            .order_by(InventoryBatch.expiry_date.asc(), InventoryBatch.received_at.asc())
        ).scalars()
        for batch in candidates:
            available = batch.quantity_on_hand - batch.reserved_quantity
            if available <= 0:
                continue
            allocated = min(required, available)
            allocations.append((item, batch, allocated))
            required -= allocated
            if required <= 0:
                break
        if required > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient inventory for prescription")

    dispensing_items: list[DispensingItem] = []
    for item, batch, allocated in allocations:
        quantity_before = batch.quantity_on_hand
        reserved_before = batch.reserved_quantity
        batch.reserved_quantity += allocated
        batch.version += 1
        batch.updated_by = actor.id
        dispensing_item = DispensingItem(
            dispensing_record_id=dispensing_record_id,
            prescription_item_id=item.id,
            medication_id=item.medication_id,
            inventory_batch_id=batch.id,
            prescribed_quantity=allocated,
            dispensed_quantity=allocated,
            unit=item.dose_unit,
        )
        db.add(dispensing_item)
        dispensing_items.append(dispensing_item)
        write_inventory_transaction(
            db,
            batch,
            transaction_type=InventoryTransactionType.RESERVE,
            quantity=allocated,
            quantity_before=quantity_before,
            quantity_after=batch.quantity_on_hand,
            reserved_before=reserved_before,
            reserved_after=batch.reserved_quantity,
            reference_type="dispensing_record",
            reference_id=dispensing_record_id,
            reason="Reserve inventory for dispensing",
            actor=actor,
        )
    return dispensing_items


def release_dispensing_inventory(db: Session, dispensing_items: list[DispensingItem], actor: User, reason: str) -> None:
    for item in dispensing_items:
        if item.inventory_batch_id is None:
            continue
        batch = get_batch(db, item.inventory_batch_id)
        quantity_before = batch.quantity_on_hand
        reserved_before = batch.reserved_quantity
        release_quantity = min(item.prescribed_quantity, batch.reserved_quantity)
        batch.reserved_quantity -= release_quantity
        batch.version += 1
        batch.updated_by = actor.id
        write_inventory_transaction(
            db,
            batch,
            transaction_type=InventoryTransactionType.RELEASE,
            quantity=release_quantity,
            quantity_before=quantity_before,
            quantity_after=batch.quantity_on_hand,
            reserved_before=reserved_before,
            reserved_after=batch.reserved_quantity,
            reference_type="dispensing_record",
            reference_id=item.dispensing_record_id,
            reason=reason,
            actor=actor,
        )


def dispense_reserved_inventory(db: Session, dispensing_items: list[DispensingItem], actor: User) -> None:
    for item in dispensing_items:
        if item.inventory_batch_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing item has no inventory batch")
        batch = get_batch(db, item.inventory_batch_id)
        if item.dispensed_quantity <= 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensed quantity must be greater than zero")
        if item.dispensed_quantity > item.prescribed_quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensed quantity cannot exceed reserved quantity")
        if batch.reserved_quantity < item.prescribed_quantity or batch.quantity_on_hand < item.dispensed_quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inventory changed before hand-out")
        quantity_before = batch.quantity_on_hand
        reserved_before = batch.reserved_quantity
        batch.quantity_on_hand -= item.dispensed_quantity
        batch.reserved_quantity -= item.prescribed_quantity
        batch.version += 1
        batch.updated_by = actor.id
        write_inventory_transaction(
            db,
            batch,
            transaction_type=InventoryTransactionType.DISPENSE,
            quantity=item.dispensed_quantity,
            quantity_before=quantity_before,
            quantity_after=batch.quantity_on_hand,
            reserved_before=reserved_before,
            reserved_after=batch.reserved_quantity,
            reference_type="dispensing_record",
            reference_id=item.dispensing_record_id,
            reason="Dispense medication",
            actor=actor,
        )
