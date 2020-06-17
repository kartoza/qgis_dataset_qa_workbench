import datetime as dt
import json
import typing
import uuid
from enum import Enum

import qgis.core
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt, QAbstractItemModel

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


class TreeNode:

    def __init__(self, parent, row):
        self.parent = parent
        self.row = row
        self.sub_nodes = self._get_children()

    def _get_children(self):
        raise NotImplementedError


class TreeModel(QAbstractItemModel):

    def __init__(self):
        super().__init__()
        self.root_nodes = self._get_root_nodes()

    def _get_root_nodes(self):
        raise NotImplementedError

    def index(self, row: int, column: int, parent: typing.Optional[QtCore.QModelIndex] = None):
        if not parent.isValid():
            result = self.createIndex(row, column, self.root_nodes[row])
        else:
            parent_node: TreeNode = parent.internalPointer()
            result = self.createIndex(row, column, parent_node.sub_nodes[row])
        return result

    def parent(self, index: QtCore.QModelIndex):
        if not index.isValid():
            result = QtCore.QModelIndex()
        else:
            node: TreeNode = index.internalPointer()
            if node.parent is None:
                result = QtCore.QModelIndex()
            else:
                result = self.createIndex(node.parent.row, 0, node.parent)
        return result

    def reset(self):
        self.root_nodes = self._get_root_nodes()
        super().reset()

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        if not parent.isValid():
            result = len(self.root_nodes)
        else:
            node: TreeNode = parent.internalPointer()
            result = len(node.sub_nodes)
        return result


class ChecklistItemProperty:
    name: str
    value: typing.Any

    def __init__(self, name: str, value: typing.Any):
        self.name = name
        self.value = value


class ChecklistItemHead:
    name: str
    validated: bool
    check_properties: typing.List

    def __init__(self, name: str, check_properties: typing.List[ChecklistItemProperty]):
        self.name = name
        self.validated = False
        self.check_properties = check_properties

    @classmethod
    def from_dict(cls, raw: typing.Dict):
        check_properties = [
            ChecklistItemProperty('description', raw.get('description')),
            ChecklistItemProperty('guide', raw.get('guide')),
            ChecklistItemProperty('automation', raw.get('automation')),
            ChecklistItemProperty('notes', ''),
        ]
        return cls(raw['name'], check_properties)


class NewCheckList:
    identifier: uuid.UUID
    name: str
    description: str
    dataset_type: DatasetType
    validation_artifact_type: ValidationArtifactType
    checks: typing.List[ChecklistItemHead]

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
                checklist_head = ChecklistItemHead.from_dict(raw_check)
            except KeyError:
                raise
            instance.checks.append(checklist_head)
        return instance


def new_load_checklists() -> typing.List[NewCheckList]:
    directory = utils.get_checklists_dir()
    result = []
    for item in directory.iterdir():
        log_message(f'loading file {item}...')
        if item.is_file():
            with item.open(encoding="utf-8") as fh:  # TODO: use the same encoding used by QGIS
                try:
                    raw_data = json.load(fh)
                    checklist = NewCheckList.from_dict(raw_data)
                    result.append(checklist)
                except (UnicodeDecodeError, ValueError, KeyError) as exc:
                    log_message(f'Could not generate checklist from {str(item)!r} because: {exc}')
    return result


class ChecklistItemPropertyNode(TreeNode):
    ref: ChecklistItemProperty

    def __init__(self, ref: ChecklistItemProperty, parent, row):
        self.ref = ref
        super().__init__(parent, row)

    def _get_children(self):
        return []


class ChecklistItemHeadNode(TreeNode):
    ref: ChecklistItemHead

    def __init__(self, ref: ChecklistItemHead, parent, row):
        self.ref = ref
        super().__init__(parent, row)

    def _get_children(self):
        result = []
        for index, check_property in enumerate(self.ref.check_properties):
            check_property_node = ChecklistItemPropertyNode(check_property, self, index)
            result.append(check_property_node)
        return result


class CheckListItemsModel(TreeModel):
    root_nodes: typing.List[ChecklistItemHead]

    def __init__(self, root_elements: typing.List[ChecklistItemHead]):
        self.root_elements = root_elements
        super().__init__()

    def _get_root_nodes(self):
        result = []
        for index, check_head in enumerate(self.root_elements):
            check_head_node = ChecklistItemHeadNode(check_head, None, index)
            result.append(check_head_node)
        return result

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: Qt = Qt.DisplayRole) -> typing.Any:
        result = None
        if index.isValid():
            node = index.internalPointer()
            if isinstance(node, ChecklistItemHeadNode):
                check_head: ChecklistItemHead = node.ref
                if role == Qt.DisplayRole:
                    if index.column() == 0:
                        result = check_head.name
                    elif index.column() == 1:
                        result = check_head.validated
                    else:
                        raise RuntimeError(f'Invalid column: {index.column()}')
            else:  # it is a checklist property
                check_property: ChecklistItemProperty = node.ref
                if role == Qt.DisplayRole:
                    if index.column() == 0:
                        result = check_property.name
                    elif index.column() == 1:
                        result = check_property.value
                    else:
                        raise RuntimeError(f'Invalid column: {index.column()}')
        return result

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt = Qt.DisplayRole) -> typing.Any:
        result = None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                result = 'Check'
            elif section == 1:
                result = 'Validated'
        return result

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        result = super().flags(index)
        if index.isValid():
            node = index.internalPointer()
            if index.parent() == QtCore.QModelIndex():
                checklist_head: ChecklistItemHead = node.ref
                if index.column() == 0:
                    result = result | Qt.ItemIsEditable
                elif index.column() == 1:
                    result = result | Qt.ItemIsUserCheckable
            else:
                checklist_property: ChecklistItemProperty = node.ref
                if index.column() == 1:
                    result = result | Qt.ItemIsEditable
        return result

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int) -> bool:
        result = False
        if index.isValid():
            node = index.internalPointer()
            if index.parent() == QtCore.QModelIndex():
                checklist_head: ChecklistItemHead = node.ref
                if index.column() == 0 and role == Qt.EditRole:
                    checklist_head.name = value
                    self.dataChanged.emit(index, index, [role])
                    result = True
        return result


class ChecklistItemsModelDelegate(QtWidgets.QStyledItemDelegate):

    def paint(
        self,
        painter: QtGui.QPainter,
        option: 'QStyleOptionViewItem',
        index: QtCore.QModelIndex
    ) -> None:
        if index.isValid():
            if not index.parent().isValid():
                checklist_item_head: ChecklistItemHead = index.internalPointer()
                if index.column() == 1:
                    pass
