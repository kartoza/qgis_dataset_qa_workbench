https://github.com/kartoza/qgis_dataset_qa_workbench/workflows/github%20pages/badge.svg

# QGIS Dataset QA Workbench

A QGIS3 plugin for assisting in dataset quality assurance workflows.

This plugin allows loading checklists with steps that should be verified 
when doing dataset quality assurance (QA). Checklist items can be automated 
by using QGIS Processing algorithms


## Install

This plugin can be installed directly by QGIS. 

For now it is distributed by means of a custom plugin repository. In order 
to install it you need to add the repository to QGIS' plugin manager 
(_Plugins -> Manage and Install Plugins... -> Settings -> 
Plugin repositories -> Add..._). 

The repository URL is:

https://kartoza.github.io/qgis_dataset_qa_workbench/repo/plugins.xml

After adding the plugin repo, the plugin manager will refresh its list of 
plugins automatically. Now search for a plugin called `Dataset QA Worbench` 
and install it.

We recommend also installing the [QGIS Resource Sharing] plugin, since it
is able to share the checklists that are required by  our plugin.


## Quickstart

### 0. Add sample checklist repository

After having installed both this plugin and the [QGIS Resource Sharing] 
plugin, add a new repo to QGIS Resource Sharing:
   
1. Navigate to _Plugins -> Resource Sharing -> Resource Sharing_

1. On the QGIS Resource Sharing dialog, go to _Settings -> Add repository..._

1. Add the following repository:
   
   -  Name: QGIS Dataset QA Workbench demo
   -  URL: https://github.com/kartoza/qgis_dataset_qa_workbench.git
   -  Authentication: (Leave it blank)
     
1. The new _QGIS Dataset QA Workbench demo_ repository shall now be 
   displayed by the Resource Sharing plugin
   
1. Navigate to the  _All collections_ section and look for an entry named
   _QGIS Dataset QA Workbench demo_
     
1. Press the _Install_ button. The Resource Sharing plugin proceeds to 
   download and install some sample checklists to the 
   `{qgis-user-profile-dir}/checklists` directory.
     
     
### 1. Choose checklist to perform validation with
     
1. Open the QGIS Dataset QA Workbench dock (navigate to 
   _Plugins -> Dataset QA Workbench -> Dataset QA Workbench_ or click the 
   plugin's icon) and navigate to the _Choose Checklist_ tab
   
1. Inside the plugin dock, navigate to _Choose Checklist -> Choose..._. 

   In the dialog that opens, select one of the existing checklists. Take into
   account the dataset type that it is applicable to (_vector_ or _raster_) and
   the artifact that it applies to (_dataset_ or _style_). Click the _OK_ button 
   to close this dialog. The checklist is loaded and is ready to use.
   
1. Select if you want to

   - a) Validate one of the currently loaded layers. If so, be sure to select 
     it on the list of layers shown in the plugin dock
     
   - b) Validate an external file, by indicating its path on the local filesystem
   
   Upon selecting one of these options, both the _Perform Validation_ and 
   _Generate Report_ tabs become selectable
   
   
### 2. Perform validation of a resource

Move over to the _Perform Validation_ tab. For each of check on the checklist:

1. Read the check's _description_ in order to understand what the current 
   check is about
   
1. The check's _guide_ section should have a detailed practical description 
   on how to go about performing the check validation manually.
   
1. A checklist check can be validated in one of two ways:

   - Manually - Follow the instructions provided by the _guide_ section. 
     These should be detailed and practical enough in order to allow you to 
     properly validate the current checklist check.
     
     
   - Automatically - If applicable, the validation may be performed by 
     pressing one of the two buttons present on the _automation_ section.
     
     -  _Run_ - Perform validation by using whatever predefined parameters have 
        been used by the checklist's designer
        
     -  _Configure and run..._ - Configure the check's validation parameters 
        and then run the validation procedure
        
1. After performing validation, you may optionally click the 
   _Validation notes_ section and type down any relevant notes about the 
   process.


### 3. Generate validation report

After having validated all of the checklist's checks, move over to the 
_Generate Report_ tab. This tab displays a report on the validation, with
information related to:

- the dataset being validated
- the overall validation result
- result of each check


     
   
   
## Creating a new checklist

Creating a new checklist is a matter of creating a new `.json` file and 
placing it in the `{qgis-user-profile-dir}/checklists` directory.

Checklists are specified in [json] and must obey to the [checklist schema].

Example checklist definition:

```json
{
  "name": "Sample checklist",
  "description": "This is just a sample checklist - be sure to delete it",
  "dataset_type": "vector",
  "validation_artifact_type": "dataset",
  "checks": [
    {
      "name": "geometry is valid",
      "description": "Layer's geometry does not have invalid geometries.",
      "guide": "Navigate to Vector -> Geometry tools -> Check Validity... and run the validity analysis tool. Afterwards check that there are no features on the `invalid output` layer",
      "automation": {
        "algorithm_id": "qgis:checkvalidity",
        "artifact_parameter_name": "INPUT_LAYER",
        "output_name": "INVALID_COUNT",
        "negate_output": true
      }
    }
  ]
}
```

### Validating checklists

The [checklist schema] file is a [JSON Schema] file with the 
definition of a Checklist. It can be used to check if new checklists
are correctly defined. 

Either use the `jsonschema` python package (which is pulled when 
doing a `pipenv install`) or use any online json schema validator. [Your IDE] 
might also support validating json files with a json schema.

Example:

```
# validating checklist with local jsonschema package
pipenv run jsonschema -i checklist-file.json schemas/checklist-check.json
```


## Development

This plugin uses [pipenv] and [paver] for development.

An easy way to get started is to (fork and) clone this repo, install pipenv 
and install it!

```
sudo apt install pyqt5-dev-tools

# create your virtualenv but use system site-packages too
# this is in order to use QGIS python bindings in the venv
pipenv --site-packages
PIP_IGNORE_INSTALLED=1 pipenv install
```

### Installing locally

Call the `install` task:

```
pipenv run paver install
```


### Running tests

Be sure to install the development dependencies:

```
PIP_IGNORE_INSTALLED=1 pipenv install --dev
```

Install the plugin and then run the test suite

```
pipenv run paver install
pipenv shell
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
python -m pytest -v -x ~/dev/qgis_dataset_qa_workbench
```


### Publishing a new version

TBD



## Attribution

This plugin uses icons from the [Font Awesome] project. Icons are used as-is, without any modification, 
in accordance with their [license]

[QGIS Resource Sharing]: https://github.com/QGIS-Contribution/QGIS-ResourceSharing
[json]: https://www.json.org/json-en.html
[checklist schema]: https://raw.githubusercontent.com/kartoza/qgis_dataset_qa_workbench/master/schemas/checklist-check.json
[Font Awesome]: https://fontawesome.com/
[license]: https://fontawesome.com/license
[pipenv]: https://pipenv.pypa.io/en/latest/
[paver]: https://pythonhosted.org/Paver/index.html
[jsonschema]: https://json-schema.org/
[Your IDE]: https://www.jetbrains.com/help/pycharm/json.html#ws_json_schema_add_custom
