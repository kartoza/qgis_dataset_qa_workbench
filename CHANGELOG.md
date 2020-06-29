# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

-  Checklist definition is more flexible with automation specification
-  Validation report is now saved as a PDF file


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


[unreleased]: https://github.com/kartoza/qgis_checklist_checker/compare/v0.4.0...master
[0.3.2]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.4.0
[0.3.2]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.2
[0.3.1]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.1
[0.3.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.3.0
[0.2.1]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.2.1
[0.2.0]: https://github.com/kartoza/qgis_checklist_checker/-/tags/v0.2.0
