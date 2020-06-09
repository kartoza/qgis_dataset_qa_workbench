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


class Checklist:
    identifier: uuid.UUID
    name: str
    description: str
    dataset_types: typing.List[DatasetType]
    validation_artifact_types: typing.List[ValidationArtifactType]
    checks: typing.List[ChecklistItem]

    def __init__(
            self,
            name: str,
            description: str,
            dataset_types: typing.Optional[typing.List[DatasetType]] = None,
            validation_artifact_types: typing.Optional[typing.List[ValidationArtifactType]] = None
    ):
        self.identifier = uuid.uuid4()
        self.name = name
        self.description = description
        self.dataset_types = list(dataset_types) if dataset_types is not None else list(DatasetType)
        self.validation_artifact_types = list(
            validation_artifact_types) if validation_artifact_types is not None else list(ValidationArtifactType)
        self.checks = []

    @classmethod
    def from_dict(cls, raw: typing.Dict):
        dataset_types = [DatasetType(i) for i in raw.get('dataset_types', [])]
        validation_artifact_types = [ValidationArtifactType(i) for i in raw.get('validation_artifact_types', [])]
        try:
            instance = cls(
                name=raw['name'],
                description=raw.get('description', ''),
                dataset_types=dataset_types,
                validation_artifact_types=validation_artifact_types
            )
        except KeyError:
            raise
        for raw_check in raw.get('checks', []):
            try:
                check = ChecklistItem(
                    name=raw_check['name'],
                    description=raw_check.get('description', ''),
                    guide=raw_check.get('guide', ''),
                    automation=raw_check.get('automation'),
                )
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
        if item.is_file():
            try:
                with item.open(encoding="utf-8") as fh:  # TODO: use the same encoding used by QGIS
                    raw_data = json.load(fh)
                    try:
                        checklist = Checklist.from_dict(raw_data)
                    except ValueError as exc:
                        log_message(f'Could not generate checklist from {str(item)!r} because: {exc}')
                    result.append(checklist)
            except IOError as err:
                log_message(err)
    return result
