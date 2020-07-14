import pytest

from dataset_qa_workbench.datasetqaworkbench import dataset_qa_workbench_dock
from dataset_qa_workbench.datasetqaworkbench.constants import TabPages


@pytest.mark.parametrize('tab_index, expected', [
    pytest.param(TabPages.CHOOSE.value, True),
    pytest.param(TabPages.VALIDATE.value, False),
    pytest.param(TabPages.REPORT.value, False),
])
def test_tab_widget_page_initial_state(iface, tab_index, expected):
    dock = dataset_qa_workbench_dock.DatasetQaWorkbenchDock(iface)
    page = dock.tab_widget.widget(tab_index)
    assert page.isEnabled() == expected


@pytest.mark.parametrize('widget_name, expected', [
    pytest.param('choose_checklist_pb', True),
    pytest.param('checklist_name_le', False),
    pytest.param('checklist_types_le', False),
    pytest.param('checklist_description_te', False),
    pytest.param('validate_layer_rb', False),
    pytest.param('layer_chooser_lv', False),
    pytest.param('validate_file_rb', False),
    pytest.param('file_chooser', False),
])
def test_dock_widgets_initial_state(iface, widget_name, expected):
    dock = dataset_qa_workbench_dock.DatasetQaWorkbenchDock(iface)
    widget = getattr(dock, widget_name)
    assert widget.isEnabled() == expected


def test_initial_tab_page_is_choose_checklist(iface):
    dock = dataset_qa_workbench_dock.DatasetQaWorkbenchDock(iface)
    assert dock.tab_widget.currentIndex() == TabPages.CHOOSE.value