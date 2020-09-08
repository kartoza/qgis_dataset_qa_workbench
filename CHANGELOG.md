# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


-  Added some automated tests
-  Improved documentation on README
-  Added sample checklists as a custom QGIS Resource Sharing plugin repository


## [0.5.4] - 2020-07-08

### Added

-  Double clicking the checklist now accepts the checklist chooser dialog

### Fixed

-  Fix crashes when adding/removing layers and the plugin is activated
-  Fix saved checklist contains extra properties that cause jsonschema validation errors
-  The GUI no longer offers to put validation report on layer's metadata properties when using a non-layer resource


## [0.5.3] - 2020-07-01

### Fixed

-  Fix incorrect URL for default checklist server


## [0.5.2] - 2020-07-01

### Fixed

-  Fix invalid CD configuration


## [0.5.1] - 2020-07-01

### Added

-  CI badge to the README

### Fixed

-  Fix invalid CD configuration


## [0.5.0] - 2020-06-30

### Added
-  Add button to run all automatable checks at once
-  Add button to uncheck all previously checked checklist items
-  Add json schema file with the checklist definition - This allows validation of user-created checklists
-  Add icon to processing provider and algorithms
-  Allow performing validation on external files

### Changed
-  Checklist definition is more flexible with automation specification
-  Validation report is now saved as a PDF file
-  Rename plugin to _Dataset QA Workbench_

### Fixed

-  Fix `clear_all_checks` button not clearing validation notes


## [0.4.0] - 2020-06-25

### Added

-  Add report to layer metadata
-  Add user name and timestamp to report
-  Add new checklist servers
-  Edit existing checklist servers name and URL

### Fixed

-  Improve sizing of checklist columns
-  Toggle access of buttons depending on current state of user interface


## [0.3.2] - 2020-06-24

### Fixed

-  Fix typo in checklist definition file for GeoCRIS


## [0.3.1] - 2020-06-24

### Fixed

-  Change the version to match tag name


## [0.3.0] - 2020-06-24

### Added

-  Allow configuration of automation in the checklist definition file
-  Processing algorithm for checking a layer's CRS against a target CRS

### Fixed

-  Checklist definition file no longer contains `validation_notes`


## [0.2.1] - 2020-06-23

### Fixed

-  Fix typo in workflow file that prevented build to finish correctly

## [0.2.0] - 2020-06-23

### Added

-  Initial support for automation of checklist steps
-  Perform validation of loaded map layers
-  Generate report in JSON format
-  Load checklists from remote server
-  Default server with checklists for GeoCRIS
-  Paver file for development
-  Initial project structure


[unreleased]: https://github.com/kartoza/qgis_checklist_checker/compare/v0.5.4...master
[0.5.3]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.5.4
[0.5.3]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.5.3
[0.5.2]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.5.2
[0.5.1]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.5.1
[0.5.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.5.0
[0.4.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.4.0
[0.3.2]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.2
[0.3.1]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.1
[0.3.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.0
[0.2.1]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.2.1
[0.2.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.2.0
