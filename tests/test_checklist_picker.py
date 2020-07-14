import pytest
from PyQt5 import QtGui

from dataset_qa_workbench.datasetqaworkbench import checklist_picker


@pytest.mark.parametrize('button_type, expected', [
    pytest.param('Ok', False),
    pytest.param('Cancel', True)
])
def test_checklist_picker_initial_button_box_state(iface, button_type, expected):
    picker = checklist_picker.ChecklistPicker(iface)
    button = picker.button_box.button(getattr(picker.button_box, button_type))
    assert button.isEnabled() == expected


def test_selecting_a_checklist_enables_ok_button(iface, qtbot):
    picker = checklist_picker.ChecklistPicker(iface)
    print(f'num_checklists: {picker.checklists_tv.model().rowCount()}')
    picker.show()
    qtbot.addWidget(picker)
