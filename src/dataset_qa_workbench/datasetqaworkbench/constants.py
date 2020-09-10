from enum import Enum

from PyQt5.QtCore import Qt

SETTINGS_GROUP = 'PythonPlugins/dataset_qa_workbench'

QGIS_VARIABLE_PREFIX = 'dataset_qa_workbench'

class DatasetType(Enum):
    DOCUMENT = "document"
    RASTER = "raster"
    VECTOR = "vector"


class ValidationArtifactType(Enum):
    DATASET = "dataset"
    METADATA = "metadata"
    STYLE = "style"


class TabPages(Enum):

    CHOOSE = 0
    VALIDATE = 1
    REPORT = 2


class ChecklistModelColumn(Enum):
    IDENTIFIER = 0
    NAME = 1
    DATASET_TYPE = 2
    APPLICABLE_TO = 3


class ChecklistItemPropertyColumn(Enum):
    DESCRIPTION = 0
    GUIDE = 1
    AUTOMATION = 2
    VALIDATION_NOTES = 3


class LayerChooserDataRole(Enum):
    LAYER_IDENTIFIER = Qt.UserRole + 1


class CustomDataRoles(Enum):
    LAYER_CHOOSER_LAYER_IDENTIFIER = Qt.UserRole + 1
    CHECKLIST_DOWNLOADER_IDENTIFIER = Qt.UserRole + 2
