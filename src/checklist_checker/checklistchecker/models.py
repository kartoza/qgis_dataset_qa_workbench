import json
import typing
import uuid
from enum import Enum

import qgis.core
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt

from . import utils
from .utils import log_message
from .constants import DatasetType, ValidationArtifactType


class ChecklistItem:
    name: str
    description: str
    guide: str
    validated: bool = False
    automation = None
    notes: str

    def __init__(self, name: str, description: str, guide: str, automation=None):
        self.name = name
        self.description = description
        self.guide = guide
        self.validated = False
        self.automation = automation
        self.notes = ''

    @classmethod
    def from_dict(cls, raw: typing.Dict):
        instance = cls(
            name=raw['name'],
            description=raw.get('description', ''),
            guide=raw.get('guide', ''),
            automation=raw.get('automation', '')
        )
        return instance


# TODO - In order to simplify things, a single checklist will only be applicable to one dataset type and one validation artifact
class Checklist:
    identifier: uuid.UUID
    name: str
    description: str
    dataset_type: DatasetType
    validation_artifact_type: ValidationArtifactType
    checks: typing.List[ChecklistItem]

    def __init__(
            self,
            name: str,
            description: str,
            dataset_type: DatasetType,
            validation_artifact_type: ValidationArtifactType
    ):
        self.identifier = uuid.uuid4()
        self.name = name
        self.description = description
        self.dataset_type = dataset_type
        self.validation_artifact_type = validation_artifact_type
        self.checks = []

    @classmethod
    def from_dict(cls, raw: typing.Dict):
        try:
            instance = cls(
                name=raw['name'],
                description=raw.get('description', ''),
                dataset_type=DatasetType(raw['dataset_type']),
                validation_artifact_type=ValidationArtifactType(raw['validation_artifact_type'])
            )
        except KeyError:
            raise
        for raw_check in raw.get('checks', []):
            try:
                check = ChecklistItem.from_dict(raw_check)
            except KeyError:
                raise
            instance.checks.append(check)
        return instance


class ChecklistModel(QStandardItemModel):

    def __init__(
            self,
            checklist: Checklist,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        root = self.invisibleRootItem()
        for check in checklist.checks:
            check.setFlags(Qt.ItemIsEnabled)
            root.appendRow(check)
        self.setHorizontalHeaderLabels(['check'])

    # def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
    #     # reimplement this in oder to set data on the checklist model
    #     # with the `index` we should be able to retrieve the relevant checklist step
    #     result = {
    #         Qt.EditRole: update_data,
    #     }
    #     result = None
    #     if role == Qt.EditRole:
    #     else:
    #         result = super().setData(index, value, role)
    #     return result


    # def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
    #     # reimplement this in oder to fetch data from the checklist model
    #     return super().data(index, role)


    def add_check(self, check):
        pass


def load_checklists() -> typing.List[Checklist]:
    directory = utils.get_checklists_dir()
    result = []
    for item in directory.iterdir():
        log_message(f'loading file {item}...')
        if item.is_file():
            with item.open(encoding="utf-8") as fh:  # TODO: use the same encoding used by QGIS
                try:
                    raw_data = json.load(fh)
                    checklist = Checklist.from_dict(raw_data)
                    result.append(checklist)
                except (UnicodeDecodeError, ValueError, KeyError) as exc:
                    log_message(f'Could not generate checklist from {str(item)!r} because: {exc}')
    return result
