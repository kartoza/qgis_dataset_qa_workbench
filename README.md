# QGIS Dataset QA Workbench

A QGIS3 plugin for assisting in dataset quality assurance workflows

## Install

This plugin can be installed directly by QGIS. For now it is distributed 
by means of a custom plugin repository. In order to install it you need 
to add the repository to QGIS' plugin manager 
(_Plugins -> Manage and Install Plugins... -> Settings -> Plugin repositories -> Add..._). 
The repository URL is:

https://kartoza.github.io/qgis_dataset_qa_workbench/repo/plugins.xml

After adding the plugin repo, the plugin manager will refresh its list of 
plugins automatically. Now search for a plugin called `Dataset QA Worbench` 
and install it.


## Development

This plugin uses [pipenv] and [paver] for development.

An easy way to get started is to (fork and) clone this repo, install pipenv 
and install it!

```
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

### Publishing a new version

TBD

### Validating checklists

The `schemas/checklist-check.json` file is a [JSON Schema] file with the 
definition of the checklist. It can be used to check if new checklists
are correctly defined. Either use the `jsonschema` python package (
which is pulled when doing a `pipenv install`) or use any online json schema
validator. [Your IDE] might also support validating json files with a json schema.

```
# validating checklist with local jsonschema package
pipenv run jsonschema -i checklist-file.json schemas/checklist-check.json
```


## Attribution

This plugin uses icons from the [Font Awesome] project. Icons are used as-is, without any modification, 
in accordance with their [license]

[Font Awesome]: https://fontawesome.com/
[license]: https://fontawesome.com/license
[pipenv]: https://pipenv.pypa.io/en/latest/
[paver]: https://pythonhosted.org/Paver/index.html
[jsonschema]: https://json-schema.org/
[Your IDE]: https://www.jetbrains.com/help/pycharm/json.html#ws_json_schema_add_custom
