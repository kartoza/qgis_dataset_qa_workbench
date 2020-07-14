from pathlib import Path

from qgis.core import QgsMapLayerType
import pytest

from dataset_qa_workbench.datasetqaworkbench import utils
from dataset_qa_workbench.datasetqaworkbench.constants import DatasetType


def test_get_profile_base_path(qgis_application):
    result = utils.get_profile_base_path()
    expected = Path('~').expanduser() / '.local/share/QGIS/QGIS3/profiles/default'
    assert result == expected


def test_get_checklists_dir(qgis_application):
    result = utils.get_checklists_dir()
    assert result == Path('~').expanduser() / '.local/share/QGIS/QGIS3/profiles/default/checklists'


@pytest.mark.parametrize('maplayer_type, expected', [
    pytest.param(QgsMapLayerType.VectorLayer, DatasetType.VECTOR),
    pytest.param(QgsMapLayerType.RasterLayer, DatasetType.RASTER),
])
def test_match_maplayer_type(maplayer_type, expected):
    assert utils.match_maplayer_type(maplayer_type) == expected
