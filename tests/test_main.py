from dataset_qa_workbench.datasetqaworkbench import main


def test_plugin_is_loadable(iface):
    plugin = main.DatasetQaWorkbench(iface)