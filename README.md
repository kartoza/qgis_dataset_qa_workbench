# QGIS Checklist checker

A QGIS3 plugin for checking checklists

## Install

This plugin can be installed directly by QGIS. For now it is distributed by means of a custom plugin repository. In 
order to install it you need to add the repository to QGIS' plugin manager 
(_Plugins -> Manage and Install Plugins... -> Settings -> Plugin repositories -> Add..._). The
repo's URL is:

https://kartoza.github.io/qgis_checklist_checker/repo/plugins.xml

After adding the plugin repo, the plugin manager will refresh its list of plugins automatically. Now search for a 
plugin called `Checklist checker` and install it.


## Development

This plugin uses [pipenv] and [paver] for development.

An easy way to get started is to (fork and) clone this repo, install pipenv 
and `pipenv install --dev` it!


### Installing locally

Call the `install` task:

```

```

### Publishing a new version

TBD

[pipenv]: https://pipenv.pypa.io/en/latest/
[paver]: https://pythonhosted.org/Paver/index.html


## Attribution

This plugin uses icons from the [Font Awesome] project. Icons are used as-is, without any modification, 
in accordance with their [license]

[Font Awesome]: https://fontawesome.com/
[license]: https://fontawesome.com/license
