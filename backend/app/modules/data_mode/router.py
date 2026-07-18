from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_mode import DATA_MODE_LABELS, DataMode
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permissions
from app.modules.data_mode.schemas import (
    DataModeStatus,
    DataModeSwitchRequest,
    DataModeSwitchResponse,
    DemoDataActionRequest,
    DemoDataStatus,
)
from app.modules.data_mode.service import can_switch_data_mode, delete_demo_data, demo_status, reset_demo_data, seed_demo_data, switch_user_mode
from app.modules.users.models import User

router = APIRouter(tags=["data_mode"])


def status_for_user(user: User) -> DataModeStatus:
    mode = DataMode(user.current_data_mode)
    if not settings.ENABLE_DEMO_MODE and mode == DataMode.DEMO:
        mode = DataMode.LIVE
    return DataModeStatus(
        mode=mode,
        label=DATA_MODE_LABELS[mode],
        can_switch=can_switch_data_mode(user),
        enable_demo_mode=settings.ENABLE_DEMO_MODE,
        can_access_live=user.can_access_live,
        can_access_demo=settings.ENABLE_DEMO_MODE and user.can_access_demo,
    )


@router.get("/data-mode", response_model=DataModeStatus)
def get_data_mode(current_user: User = Depends(get_current_user)) -> DataModeStatus:
    return status_for_user(current_user)


@router.post("/data-mode/switch", response_model=DataModeSwitchResponse)
def switch_data_mode(
    payload: DataModeSwitchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataModeSwitchResponse:
    message = switch_user_mode(db, current_user, payload.mode, payload.confirmation)
    status_payload = status_for_user(current_user)
    return DataModeSwitchResponse(**status_payload.model_dump(), message=message)


@router.get("/demo-data/status", response_model=DemoDataStatus)
def get_demo_data_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("demo_data.manage")),
) -> DemoDataStatus:
    return demo_status(db)


@router.post("/demo-data/seed", response_model=DemoDataStatus)
def post_demo_seed(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("demo_data.manage")),
) -> DemoDataStatus:
    return seed_demo_data(db, current_user)


@router.post("/demo-data/reset", response_model=DemoDataStatus)
def post_demo_reset(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("demo_data.manage")),
) -> DemoDataStatus:
    return reset_demo_data(db, current_user)


@router.delete("/demo-data", response_model=DemoDataStatus)
def delete_demo(
    payload: DemoDataActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("demo_data.manage")),
) -> DemoDataStatus:
    return delete_demo_data(db, current_user, confirmation=payload.confirmation)
