from enum import Enum

from PyQt5.QtCore import Qt

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
    DESCRIPTION = 2
    DATASET_TYPES = 3
    APPLICABLE_TO = 4


class LayerChooserDataRole(Enum):
    LAYER_IDENTIFIER = Qt.UserRole + 1
