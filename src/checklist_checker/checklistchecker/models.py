import datetime as dt
import json
import typing
import uuid
from enum import Enum

import qgis.core
from PyQt5 import QtCore
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

    def __init__(self, name: str, description: str = '', guide: str = '', automation=None):
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


class ValidationReport:
    checklist: Checklist
    validation_checks: typing.List[ChecklistItem]

    def __init__(self, checklist: Checklist, validation_checks: typing.List[ChecklistItem]):
        self.checklist = checklist
        self.validation_checks = validation_checks

    @classmethod
    def from_checks_model(cls, checklist: Checklist, checks_model: QStandardItemModel):
        for check in checks_model:
            pass


class ChecklistChecksModel(QtCore.QAbstractItemModel):
    DATA_COLUMN_ROW: int = 1
    OWN_ID_SEPARATOR: str = '*'
    PARENT_ID_SEPARATOR: str = '-'
    CHECK_ID_ROLE: int = Qt.UserRole + 1

    def __init__(self, checklist: Checklist, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checklist = checklist
        # root = self.invisibleRootItem()
        # for check in self.checklist.checks:
        #     name_item = QStandardItem(check.name)
        #     root.appendRow('Name', name_item)
        #     valid_item = QStandardItem(check.validated)
        #     root.appendRow('Valid', valid_item)
        #
        #     name_item.appendRow()
        #
        #     description_item = QStandardItem(check.description)
        #     root.appendRow('Description', description_item)

    #  ---- readonly reimplementation methods

    def index(self, row: int, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        own_pointer = self.OWN_ID_SEPARATOR.join((str(row), str(column)))
        if parent.isValid():
            parent_pointer = parent.internalPointer()
            full_pointer = self.PARENT_ID_SEPARATOR.join((parent_pointer, own_pointer))
        else:
            full_pointer = own_pointer
        log_message(f'full_pointer: {full_pointer}')
        return self.createIndex(row, column, str(full_pointer))

    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:
        log_message('inside parent() method')
        invalid_index = QtCore.QModelIndex()
        if not child.isValid():
            result = invalid_index
        else:
            full_child_pointer: str = str(child.internalPointer())
            *ancestors_coords, child_own_pointer = full_child_pointer.split(self.PARENT_ID_SEPARATOR)
            if len(ancestors_coords) == 0:
                result = invalid_index
            else:
                parent_full_pointer = self.PARENT_ID_SEPARATOR.join(ancestors_coords)
                parent_row, parent_col = ancestors_coords[-1].split(self.OWN_ID_SEPARATOR)
                result = self.createIndex(int(parent_row), int(parent_col), str(parent_full_pointer))
        return result

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        # one row for the name of the check
        # one row for the validation checkbox
        if parent.isValid():
            # parent represents a check, so it has one row for each of (description, guide, automation)
            # it may have three rows (guide, description, result)
            # or it may have four rows (guide, description, automation, result)
            check_index = parent.data(role=self.CHECK_ID_ROLE)
            current_check = self.checklist.checks[check_index]
            if current_check.automation:
                result = 4
            else:
                result = 3
        else:
            # parent is not valid so we are at the first hierarchy level,
            # in this case there are as many rows as there are checks in the checklist
            result = len(self.checklist.checks)
        return result

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return 2

    def _get_current_check(self, hierarchy_level: int, index: QtCore.QModelIndex) -> ChecklistItem:
        if hierarchy_level == 1:
            current_check_index = index.row()
        elif hierarchy_level == 2:
            current_check_index = index.parent().row()
        else:
            raise RuntimeError(f'Invalid hierarchy_level: {hierarchy_level}')
        return self.checklist.checks[current_check_index]

    def _get_first_level_info(self, index:QtCore.QModelIndex, current_check: ChecklistItem):
        if index.column() == 0:
            result = current_check.name
        elif index.column() == 1:
            result = current_check.validated
        else:
            raise RuntimeError(f'Invalid column requested: {index.column()}')
        return result

    def _get_second_level_info(self, index: QtCore.QModelIndex, current_check: ChecklistItem):
        row = index.row()
        col = index.column()
        if col == 0:
            if row == 0:
                result = 'Description'
            elif row == 1:
                result = 'Guide'
            elif row == 2:
                if current_check.automation:
                    result = 'Automation'
                else:
                    result = 'Result'
            elif row == 3:
                if current_check.automation:
                    result = 'Result'
                else:
                    raise RuntimeError(f'Invalid row requested: {index.row()}')
            else:
                raise RuntimeError(f'Invalid row requested: {index.row()}')
        elif col == 1:
            if row == 0:
                result = current_check.description
            elif row == 1:
                result = current_check.guide
            elif row == 2:
                if current_check.automation:
                    result = current_check.automation
                else:
                    result = current_check.notes
            elif row == 3:
                if current_check.automation:
                    result = 'Result'
                else:
                    raise RuntimeError(f'Invalid row requested: {index.row()}')
            else:
                raise RuntimeError(f'Invalid row requested: {index.row()}')
        else:
            raise RuntimeError(f'Invalid column requested: {index.column()}')
        return result

    def _get_hierarchy_level(self, index: QtCore.QModelIndex) -> int:
        return 2 if index.parent().isValid() else 1

    def data(self, index: QtCore.QModelIndex, role: int = Qt.DisplayRole) -> typing.Any:
        result = None
        log_message(f'valid index: {index.isValid()}')
        if index.isValid():
            if role == Qt.DisplayRole:
                hierarchy_level = self._get_hierarchy_level(index)
                log_message(f'hierarchy_level: {hierarchy_level}')
                current_check = self._get_current_check(hierarchy_level, index)
                log_message(f'current_check name: {current_check.name}')
                if hierarchy_level == 1:
                    result = self._get_first_level_info(index, current_check)
                elif hierarchy_level == 2:
                    result = self._get_second_level_info(index, current_check)
                else:
                    raise RuntimeError(f'Invalid hierarchy level: {hierarchy_level}')
                log_message(f'result: {result}')
        return result

    # ----

    # ---- read/write reimplementation methods

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        # must reimplement this
        # REMEMBER to emit the `dataChanged()` signal inside this method
        try:
            current_check = self.checklist.checks[index.row()]
        except IndexError:
            current_check = ChecklistItem(
                name=f'check {len(self.checklist.checks) + 1}',
                description='',
                guide=''
            )
        if role == Qt.EditRole and index.column() == self.DATA_COLUMN_ROW:
            # yes, this may be editable. but where are we?
            if index.parent() == self.invisibleRootItem():
                pass
            else:
                pass

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        pass  # must reimplement this



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
