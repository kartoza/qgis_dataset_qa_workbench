from pathlib import Path

import pytest
import qgis.core

from qgis_interface import QgisInterface


@pytest.fixture(scope='session')
def qgis_application():
    profile_directory = Path('~').expanduser() / '.local/share/QGIS/QGIS3/profiles/default'
    qgis.core.QgsApplication.setPrefixPath('/usr', True)
    app = qgis.core.QgsApplication([], True, str(profile_directory))
    app.initQgis()
    yield app
    app.exitQgis()


@pytest.fixture()
def iface(qgis_application):
    return QgisInterface(None)
