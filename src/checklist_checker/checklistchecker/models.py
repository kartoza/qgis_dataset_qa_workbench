import json
import typing
import uuid

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from . import utils
from .constants import (
    ChecklistItemPropertyColumn,
    DatasetType,
    ValidationArtifactType,
)


class ChecklistServer:
    identifier: uuid.UUID
    name: str
    url: str

    def __init__(self, name: str, url: str, identifier: typing.Optional[uuid.UUID] = None):
        self.name = name
        self.url = url
        self.identifier = identifier or uuid.uuid4()


class ChecklistItemProperty:
    name: str
    value: typing.Any

    def __init__(self, name: str, value: typing.Any):
        self.name = name
        self.value = value


class ChecklistAutomationProperty(ChecklistItemProperty):
    algorithm_id: str
    extra_parameters: typing.Dict[str, str]

    def __init__(self, name: str, value: typing.Optional[typing.Dict] = None):
        super().__init__(name, value)
        automation_info = dict(value) if value is not None else {}
        self.algorithm_id = automation_info.get('algorithm_id')
        self.extra_parameters = automation_info.get('extra_parameters', {})

    def to_dict(self):
        if self.algorithm_id is not None:
            result = {
                'algorithm_id': self.algorithm_id,
                'extra_parameters': self.extra_parameters
            }
        else:
            result = None
        return result


class ChecklistItemHead:
    name: str
    validated: Qt.CheckState
    check_properties: typing.List

    def __init__(self, name: str, check_properties: typing.List[ChecklistItemProperty]):
        self.name = name
        self.validated = Qt.Unchecked
        self.check_properties = check_properties

    def __getattr__(self, item):
        # This method is here to make it easier to access an instance's properties.
        # It enables calling ``check.description`` in order to get an instance's
        # description, rather than having to call
        # ``check.check_properties[ChecklistItemPropertyColumn.DESCRIPTION.value].value``
        if item == ChecklistItemPropertyColumn.DESCRIPTION.name.lower():
            prop: ChecklistItemProperty = self.check_properties[ChecklistItemPropertyColumn.DESCRIPTION.value]
            result = prop.value
        elif item == ChecklistItemPropertyColumn.GUIDE.name.lower():
            prop: ChecklistItemProperty = self.check_properties[ChecklistItemPropertyColumn.GUIDE.value]
            result = prop.value
        elif item == ChecklistItemPropertyColumn.AUTOMATION.name.lower():
            prop: ChecklistAutomationProperty = self.check_properties[ChecklistItemPropertyColumn.AUTOMATION.value]
            result = prop.to_dict()
        elif item == ChecklistItemPropertyColumn.VALIDATION_NOTES.name.lower():
            prop: ChecklistItemProperty = self.check_properties[ChecklistItemPropertyColumn.VALIDATION_NOTES.value]
            result = prop.value
        else:
            raise AttributeError
        return result

    def to_dict(
        self,
        include_notes: bool = True,
        include_result: bool = True,
        include_automation: bool = False
    ):
        result = {
            'name': self.name,
            ChecklistItemPropertyColumn.DESCRIPTION.name.lower(): self.description,
            ChecklistItemPropertyColumn.GUIDE.name.lower(): self.guide,
        }
        if include_notes:
            result[self._decode_notes_column_name()] = self.validation_notes
        if include_automation:
            result[ChecklistItemPropertyColumn.AUTOMATION.name.lower()] = self.automation
        if include_result:
            result['validated'] = bool(self.validated)
        return result

    @staticmethod
    def _decode_notes_column_name():
        return ChecklistItemPropertyColumn.VALIDATION_NOTES.name.replace('_', ' ').capitalize()

    @classmethod
    def from_dict(cls, raw: typing.Dict):
        check_properties = []
        for item in sorted(ChecklistItemPropertyColumn.__members__.values(), key=lambda m: m.value):
            name = item.name.lower()
            if item == ChecklistItemPropertyColumn.AUTOMATION:
                prop = ChecklistAutomationProperty(name, raw.get(name))
            elif item == ChecklistItemPropertyColumn.VALIDATION_NOTES:
                prop = ChecklistItemProperty(cls._decode_notes_column_name(), '')
            else:
                prop = ChecklistItemProperty(name, raw.get(name))
            check_properties.append(prop)
        # check_properties = [
        #     ChecklistItemProperty(ChecklistItemPropertyColumn.DESCRIPTION.name.lower(), raw.get('description')),
        #     ChecklistItemProperty(ChecklistItemPropertyColumn.GUIDE.name.lower(), raw.get('guide')),
        #     # ChecklistItemProperty(ChecklistItemPropertyColumn.AUTOMATION.name.lower(), raw.get('automation')),
        #     ChecklistAutomationProperty(ChecklistItemPropertyColumn.AUTOMATION.name.lower(), raw.get('automation')),
        #     ChecklistItemProperty(cls._decode_notes_column_name(), ''),
        # ]
        return cls(raw['name'], check_properties)


class CheckList:
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

    def to_dict(
        self,
        include_check_notes: bool = True,
        include_check_results: bool = True,
        include_check_automation: bool = False
    ):
        result = {
            'identifier': str(self.identifier),
            'name': self.name,
            'description': self.description,
            'dataset_type': self.dataset_type.value,
            'validation_artifact_type': self.validation_artifact_type.value,
            'checks': []
        }
        for check in self.checks:
            check_dict = check.to_dict(
                include_notes=include_check_notes,
                include_result=include_check_results,
                include_automation=include_check_automation
            )
            result['checks'].append(check_dict)
        return result


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


class ChecklistItemPropertyNode(utils.TreeNode):
    ref: ChecklistItemProperty

    def __init__(self, ref: ChecklistItemProperty, parent, row):
        self.ref = ref
        super().__init__(parent, row)

    def _get_children(self):
        return []


class ChecklistItemHeadNode(utils.TreeNode):
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


class CheckListItemsModel(utils.TreeModel):
    checklist: CheckList
    root_nodes: typing.List[ChecklistItemHead]

    def __init__(self, checklist: CheckList):
        self.checklist = checklist
        super().__init__()

    @property
    def result(self):
        return all(c.validated for c in self.checklist.checks)

    def _get_root_nodes(self):
        result = []
        for index, check_head in enumerate(self.checklist.checks):
            check_head_node = ChecklistItemHeadNode(check_head, None, index)
            result.append(check_head_node)
        return result

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: Qt = Qt.DisplayRole) -> typing.Any:
        result = None
        invalid_index = QtCore.QModelIndex()
        if index.isValid():
            node = index.internalPointer()
            if index.parent() == invalid_index:
                check_head: ChecklistItemHead = node.ref
                if role == Qt.DisplayRole:
                    if index.column() == 0:
                        result = check_head.name
                    elif index.column() == 1:
                        pass
                    else:
                        raise RuntimeError(f'Invalid column: {index.column()}')
                elif role == Qt.CheckStateRole and index.column() == 1:
                    result = check_head.validated
                elif role == Qt.BackgroundRole and index.column() == 1 and check_head.validated == Qt.Checked:
                    result = QtGui.QColor(Qt.green)
            else:  # it is a checklist property
                check_head: ChecklistItemHead = index.parent().internalPointer().ref
                check_property: ChecklistItemProperty = node.ref
                if role == Qt.DisplayRole:
                    if index.column() == 0:
                        result = check_property.name
                    elif index.column() == 1:
                        if index.row() == ChecklistItemPropertyColumn.AUTOMATION.value:
                            if check_head.automation is None:
                                result = 'Not enabled'
                            else:
                                pass
                        else:
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
            if index.parent() == QtCore.QModelIndex():
                if index.column() == 1:
                    result = result | Qt.ItemIsEditable | Qt.ItemIsUserCheckable
            else:
                if index.row() == ChecklistItemPropertyColumn.VALIDATION_NOTES.value and index.column() == 1:
                    result = result | Qt.ItemIsEditable
        return result

    def setData(
        self,
        index: QtCore.QModelIndex,
        value: typing.Any,
        role: Qt.UserRole = Qt.EditRole
    ) -> bool:
        result = False
        if index.isValid():
            node = index.internalPointer()
            if index.parent() == QtCore.QModelIndex():
                checklist_head: ChecklistItemHead = node.ref
                if index.column() == 1 and role == Qt.CheckStateRole:
                    checklist_head.validated = value
                    self.dataChanged.emit(index, index, [role])
                    result = True
            else:
                checklist_property: ChecklistItemProperty = node.ref
                if index.row() == ChecklistItemPropertyColumn.VALIDATION_NOTES.value:
                    checklist_property.value = value
                    self.dataChanged.emit(index, index, [role])
                    result = True
        return result


class ChecklistItemsModelDelegate(QtWidgets.QStyledItemDelegate):
    gui_view: QtWidgets.QTreeView

    def __init__(self, gui_view: QtWidgets.QTreeView, *args, **kwargs):
        self.gui_view = gui_view
        super().__init__(*args, **kwargs)

    def sizeHint(
            self,
            option: QtWidgets.QStyleOptionViewItem,
            index: QtCore.QModelIndex
    ) -> QtCore.QSize:
        is_first_level = index.parent() == QtCore.QModelIndex()
        multiline_columns = (
            ChecklistItemPropertyColumn.DESCRIPTION.value,
            ChecklistItemPropertyColumn.GUIDE.value,
            ChecklistItemPropertyColumn.VALIDATION_NOTES.value,
        )
        is_multiline = index.row() in multiline_columns
        if not is_first_level and is_multiline and index.column() == 1:
            check_property: ChecklistItemProperty = index.internalPointer().ref
            text_to_draw = check_property.value
            base_width = self.gui_view.columnWidth(1)
            base_height = 10000  # some ridiculous high value just for initialization
            base_size = QtCore.QSize(base_width, base_height)

            metrics = QtGui.QFontMetrics(option.font)
            out_rect: QtCore.QRect = metrics.boundingRect(
                QtCore.QRect(QtCore.QPoint(0, 0), base_size),
                Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                text_to_draw
            )
            base_size.setHeight(out_rect.height())
            utils.log_message(f'final base_size height: {base_size.height()}')
            result = base_size
        else:
            result = super().sizeHint(option, index)
        return result


class MyTreeView(QtWidgets.QTreeView):

    resized = QtCore.pyqtSignal()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        self.resized.emit()


def load_checklists() -> typing.List[CheckList]:
    directory = utils.get_checklists_dir()
    result = []
    for item in directory.iterdir():
        utils.log_message(f'loading file {item}...')
        if item.is_file():
            with item.open(encoding="utf-8") as fh:  # TODO: use the same encoding used by QGIS
                try:
                    raw_data = json.load(fh)
                    checklist = CheckList.from_dict(raw_data)
                    result.append(checklist)
                except (UnicodeDecodeError, ValueError, KeyError) as exc:
                    utils.log_message(f'Could not generate checklist from {str(item)!r} because: {exc}')
    return result
