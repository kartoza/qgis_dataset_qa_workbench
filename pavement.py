import configparser
import logging
from pathlib import Path
import shlex
import shutil
import subprocess

from paver.easy import needs
from paver.easy import info, task

# TODO: - Get log level from paver's `--verbose` flag

LOCAL_ROOT_DIR = Path(__file__).parent.resolve()
SRC_NAME = LOCAL_ROOT_DIR.name.replace('qgis_', '')
PACKAGE_NAME = SRC_NAME.replace('_', '')


@task
@needs(['compile_resources'])
@needs(['generate_metadata'])
@needs(['copy_source_files'])
def deploy():
    """Deploy plugin to QGIS' plugins dir"""
    # compile resources
    # compile docs
    # make translations
    # copy things into the QGIS plugins dir
    pass


@task
@needs(['_setup_logging'])
def compile_resources():
    resources_path = LOCAL_ROOT_DIR / 'resources' / 'resources.qrc'
    qgis_root_dir = _get_qgis_root_dir()
    target_path = (
        qgis_root_dir / 'python/plugins' /
        SRC_NAME / PACKAGE_NAME / 'resources.py'
    )
    subprocess.run(shlex.split(f'pyrcc5 -o {target_path} {resources_path}'))


@task
@needs(['_setup_logging'])
def generate_metadata():
    readme_contents = _read_file('README.md')
    source_config = _get_plugin_config()
    source_general = source_config['general']
    config = configparser.ConfigParser()
    config['general'] = {
        'name': SRC_NAME.replace('_', ' ').replace('-', ' ').capitalize(),
        'qgisMinimumVersion': source_general.get(
            'qgisMinimumVersion', '3.10'),
        'description': '',  # TODO: include README's first section
        'version': _read_file('VERSION'),
        'author': source_general.get('author', ''),  # TODO: provide author from AUTHORS
        'email': source_general.get('email', ''),  # TODO: provide email from AUTHORS
        'about': readme_contents,
        'tracker': '',  # TODO: get repo URL from git,
        'repository': '',  # TODO: get repo URL from git,
        'changelog': _read_file('CHANGELOG.md'),
        'tags': source_general.get('tags', ''),
        'homepage': source_general.get('homepage', ''),
        'category': source_general.get('category', ''),
        'icon': source_general.get('icon', ''),
        'experimental': source_general.getboolean('experimental', True),
        'deprecated': source_general.getboolean('deprecated', False),
    }
    root_dir = _get_qgis_root_dir()
    target_path = root_dir / 'python/plugins' / SRC_NAME / 'metadata.txt'
    with target_path.open(mode='w') as fh:
        config.write(fh)


@task
@needs(['_setup_logging'])
def copy_source_files():
    root_dir = _get_qgis_root_dir()
    base_target_dir = root_dir / 'python/plugins' / SRC_NAME
    info(f'base_target_dir: {base_target_dir}')
    shutil.rmtree(str(base_target_dir), ignore_errors=True)
    base_target_dir.mkdir(parents=True)
    for child in (LOCAL_ROOT_DIR / 'src' / SRC_NAME).iterdir():
        info(f'child: {child}')
        target_path = base_target_dir / child.name
        info(f'target_path: {target_path}')
        handler = shutil.copytree if child.is_dir() else shutil.copy
        handler(str(child.resolve()), str(target_path))


@task
def _setup_logging():
    logging.basicConfig(level=logging.DEBUG)


@task
def _get_plugin_config():
    source_config = configparser.ConfigParser()
    source_config.read(str(LOCAL_ROOT_DIR / 'plugin_config.ini'))
    return source_config


@task
def _get_qgis_root_dir() -> Path:
    source_config = _get_plugin_config()
    profile = source_config.get('dev', 'profile')
    return Path.home() / f'.local/share/QGIS/QGIS3/profiles/{profile}'



def _read_file(relative_path: str):
    path = LOCAL_ROOT_DIR / relative_path
    with path.open() as fh:
        return fh.read()
