from enum import Enum as PythonEnum


class DataMode(str, PythonEnum):
    LIVE = "LIVE"
    DEMO = "DEMO"


DATA_MODE_LABELS: dict[DataMode, str] = {
    DataMode.LIVE: "正式資料",
    DataMode.DEMO: "假資料",
}


def normalize_data_mode(value: str | DataMode | None, *, default: DataMode = DataMode.LIVE) -> DataMode:
    if isinstance(value, DataMode):
        return value
    if not value:
        return default
    try:
        return DataMode(str(value).upper())
    except ValueError:
        return default
