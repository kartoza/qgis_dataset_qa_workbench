import typing
from pathlib import Path

import qgis.core

from .constants import DatasetType


def log_message(message, level=None):
    qgis.core.QgsMessageLog.logMessage(message)


def get_checklists_dir() -> Path:
    base_dir = get_profile_base_path()
    checklists_dir = base_dir / 'checklists'
    if not checklists_dir.is_dir():
        log_message(f'Creating checklists directory at {checklists_dir}...')
        checklists_dir.mkdir(parents=True, exist_ok=True)
    return checklists_dir


def get_profile_base_path() -> Path:
    return Path(qgis.core.QgsApplication.qgisSettingsDirPath())


def match_maplayer_type(type_: qgis.core.QgsMapLayerType) -> typing.Optional[DatasetType]:
    return {
        qgis.core.QgsMapLayerType.VectorLayer: DatasetType.VECTOR,
        qgis.core.QgsMapLayerType.RasterLayer: DatasetType.RASTER,
    }.get(type_)
