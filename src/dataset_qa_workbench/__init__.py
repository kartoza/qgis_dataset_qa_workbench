# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    from .datasetqaworkbench.main import DatasetQaWorkbench
    return DatasetQaWorkbench(iface)
