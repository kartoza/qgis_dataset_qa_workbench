import json
import typing
from pathlib import Path

import qgis.core

from . import models


def log_message(message, level=None):
    qgis.core.QgsMessageLog.logMessage(message)


def get_checklists_dir() -> Path:
    base_dir = get_profile_base_path()
    checklists_dir = base_dir / 'checklists'
    if not checklists_dir.is_dir():
        log_message(f'Creating checklists directory at {checklists_dir}...')
        checklists_dir.mkdir(parents=True, exist_ok=True)
    return checklists_dir


def load_checklists(directory: Path) -> typing.List[models.Checklist]:
    result = []
    for item in directory.iterdir():
        if item.is_file():
            try:
                with item.open(encoding="utf-8") as fh:  # TODO: use the same encoding used by QGIS
                    raw_data = json.load(fh)
                    checklist = models.Checklist.from_dict(raw_data)
                    result.append(checklist)
            except IOError as err:
                log_message(err)
    return result


def get_profile_base_path() -> Path:
    return Path(qgis.core.QgsApplication.qgisSettingsDirPath())


def match_maplayer_type(type_: qgis.core.QgsMapLayerType) -> typing.Optional[models.DatasetType]:
    return {
        qgis.core.QgsMapLayerType.VectorLayer: models.DatasetType.VECTOR,
        qgis.core.QgsMapLayerType.RasterLayer: models.DatasetType.RASTER,
    }.get(type_)
