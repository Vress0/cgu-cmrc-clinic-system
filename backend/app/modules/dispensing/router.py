from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.dispensing.models import DispensingRecord
from app.modules.dispensing.schemas import (
    DispensingHandOut,
    DispensingItemsUpdate,
    DispensingRecordRead,
    DispensingReturn,
    DispensingVerify,
    PharmacyQueueItem,
    PharmacyVisitDetail,
)
from app.modules.dispensing.service import (
    get_dispensing_record,
    get_pharmacy_visit_detail,
    hand_out_medication,
    list_pharmacy_queue,
    return_to_clinic,
    start_dispensing,
    submit_for_verification,
    update_dispensing_items,
    verify_dispensing,
)
from app.modules.users.models import User

router = APIRouter(tags=["dispensing"])


@router.get("/pharmacy/queue", response_model=list[PharmacyQueueItem])
def get_pharmacy_queue(
    session_id: UUID | None = None,
    status: str | None = Query(default=None),
    search: str = "",
    db: Session = Depends(get_db),
    _=Depends(require_permissions("pharmacy:dispense")),
) -> list[PharmacyQueueItem]:
    return list_pharmacy_queue(db, session_id=session_id, status_filter=status, search=search)


@router.get("/pharmacy/queue/{visit_id}", response_model=PharmacyVisitDetail)
def get_pharmacy_queue_item(
    visit_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("pharmacy:dispense")),
) -> PharmacyVisitDetail:
    return get_pharmacy_visit_detail(db, visit_id)


@router.post("/pharmacy/queue/{visit_id}/start", response_model=PharmacyVisitDetail)
def post_pharmacy_start(
    visit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> PharmacyVisitDetail:
    return start_dispensing(db, visit_id, current_user)


@router.get("/dispensing/{dispensing_id}", response_model=DispensingRecordRead)
def get_dispensing(
    dispensing_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return get_dispensing_record(db, dispensing_id)


@router.put("/dispensing/{dispensing_id}/items", response_model=DispensingRecordRead)
def put_dispensing_items(
    dispensing_id: UUID,
    payload: DispensingItemsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return update_dispensing_items(db, dispensing_id, payload, current_user)


@router.post("/dispensing/{dispensing_id}/submit-for-verification", response_model=DispensingRecordRead)
def post_submit_for_verification(
    dispensing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return submit_for_verification(db, dispensing_id, current_user)


@router.post("/dispensing/{dispensing_id}/verify", response_model=DispensingRecordRead)
def post_verify_dispensing(
    dispensing_id: UUID,
    payload: DispensingVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return verify_dispensing(db, dispensing_id, payload, current_user)


@router.post("/dispensing/{dispensing_id}/hand-out", response_model=DispensingRecordRead)
def post_hand_out(
    dispensing_id: UUID,
    payload: DispensingHandOut,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return hand_out_medication(db, dispensing_id, payload, current_user)


@router.post("/dispensing/{dispensing_id}/return-to-clinic", response_model=DispensingRecordRead)
def post_return_to_clinic(
    dispensing_id: UUID,
    payload: DispensingReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("pharmacy:dispense")),
) -> DispensingRecord:
    return return_to_clinic(db, dispensing_id, payload, current_user)
