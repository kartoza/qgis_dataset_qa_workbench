from typing import Dict, List, Union
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt


class Checklist:
    name: str
    description: str
    checks: List = None

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.checks = []

    @classmethod
    def from_dict(cls, raw: Dict):
        try:
            instance = cls(
                name=raw['name'],
                description=raw.get('description', '')
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

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        # reimplement this in oder to set data on the checklist model
        # with the `index` we should be able to retrieve the relevant checklist step
        result = {
            Qt.EditRole: update_data,
        }
        result = None
        if role == Qt.EditRole:
        else:
            result = super().setData(index, value, role)
        return result


    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        # reimplement this in oder to fetch data from the checklist model
        return super().data(index, role)


    def add_check(self, check):
        pass

