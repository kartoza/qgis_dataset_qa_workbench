# QGIS Dataset QA Workbench Plugin

{some inspirational screenshot}

A QGIS3 plugin for assisting in dataset quality assurance workflows.

{badges}

---

**Documentation:** [https://kartoza.github.io/qgis_dataset_qa_workbench](https://kartoza.github.io/qgis_dataset_qa_workbench)

**Source code:** [https://github.com/kartoza/qgis_dataset_qa_workbench](https://github.com/kartoza/qgis_dataset_qa_workbench)

---

This plugin allows loading checklists with steps that should be verified when doing 
dataset quality assurance (QA). Checklist items can be automated by using QGIS 
Processing algorithms.


## Installation

This plugin can be installed directly by QGIS. It is published in the
[official QGIS plugins repository]. Use the QGIS plugin manager
(navigate to _Plugins -> Manage and Install Plugins..._) and search for
_Dataset QA Workbench_. Then install the plugin.

!!! note 
    Be sure to have the _Show also experimental plugins_ checkbox checked, in the 
    plugin manager _Settings_ section.

We recommend also installing the [QGIS Resource Sharing] plugin, since it
is able to share the checklists that are required by  our plugin.


### Alternative: Custom QGIS plugin repo

We also have a custom QGIS plugins repository setup where we may publish additional
intermediary versions. It is available at:

[https://kartoza.github.io/qgis_dataset_qa_workbench/repo/plugins.xml](https://kartoza.github.io/qgis_dataset_qa_workbench/repo/plugins.xml)

1. Add this custom repository inside QGIS plugin manager
2. Refresh the list of available plugins
2. Search for a plugin named **QGIS GeoNode**
2. Install it!

Check the [Development](development.md) section for a more developer oriented 
installation procedure 


## License

This plugin is distributed under the terms of the 
[GNU General Public License version 3](https://www.gnu.org/licenses/gpl-3.0.en.html)


## Attribution

This plugin uses icons from the [Font Awesome] project. Icons are used as-is,
without any modification, in accordance with their [license].

[official QGIS plugins repository]: https://plugins.qgis.org/
[QGIS Resource Sharing]: https://qgis-contribution.github.io/QGIS-ResourceSharing/
[Font Awesome]: https://fontawesome.com/
[license]: https://fontawesome.com/license
