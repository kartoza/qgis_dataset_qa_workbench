import typing
from enum import Enum
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt


class DatasetType(Enum):
    DOCUMENT = "document"
    RASTER = "raster"
    VECTOR = "vector"


class ValidationArtifactType(Enum):
    DATASET = "dataset"
    METADATA = "metadata"
    STYLE = "style"


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

