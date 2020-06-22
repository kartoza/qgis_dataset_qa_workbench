import configparser
import datetime as dt
import json
import shlex
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from paver.easy import needs
from paver.easy import (
    cmdopts,
    environment,
    info,
    no_help,
    task,
)

# TODO: - Replace paver with click

LOCAL_ROOT_DIR = Path(__file__).parent.resolve()
SRC_NAME = 'checklist_checker'
PACKAGE_NAME = SRC_NAME.replace('_', '')


@task
@needs(['uninstall'])
def install():
    """Deploy plugin to QGIS' plugins dir"""
    temp_dir = Path(tempfile.mkdtemp())
    temp_contents_dir = temp_dir / SRC_NAME
    environment.temp_contents_dir = temp_contents_dir
    prepare_deployment()
    base_target_dir = _get_qgis_root_dir() / 'python/plugins' / SRC_NAME
    shutil.copytree(temp_contents_dir, base_target_dir)
    shutil.rmtree(temp_dir)


@task
def uninstall():
    """Remove plugin from QGIS' plugins directory"""
    root_dir = _get_qgis_root_dir()
    base_target_dir = root_dir / 'python/plugins' / SRC_NAME
    shutil.rmtree(str(base_target_dir), ignore_errors=True)


@task
@cmdopts([
    ('repo_base_url=', 'r', 'Base URL of the repository to use when generating the plugin\'s download URL'),
])
def deploy_local_repo(options):
    """Deploy plugin into a local plugin repo"""
    try:
        base_url = options.deploy_local_repo.repo_base_url
    except AttributeError:
        base_url = 'http://localhost:8000'
    temp_dir = Path(tempfile.mkdtemp())
    environment.temp_dir = temp_dir
    repo_base_dir = LOCAL_ROOT_DIR / 'docs' / 'repo'
    repo_base_dir.mkdir(parents=True, exist_ok=True)
    zip_path = generate_zip()
    shutil.copy(zip_path, repo_base_dir)
    contents_template = """
    <?xml version = '1.0' encoding = 'UTF-8'?>
    <plugins>
        <pyqgis_plugin name="{name}" version="{version}">
            <description><![CDATA[{description}]]></description>
            <about><![CDATA[{about}]]></about>
            <version>{version}</version>
            <qgis_minimum_version>{qgis_minimum_version}</qgis_minimum_version>
            <homepage><![CDATA[{homepage}]]></homepage>
            <file_name>{filename}</file_name>
            <icon>{icon}</icon>
            <author_name><![CDATA[{author}]]></author_name>
            <download_url>{download_url}</download_url>
            <update_date>{update_date}</update_date>
            <experimental>{experimental}</experimental>
            <deprecated>{deprecated}</deprecated>
            <tracker><![CDATA[{tracker}]]></tracker>
            <repository><![CDATA[{repository}]]></repository>
            <tags><![CDATA[{tags}]]></tags>
            <server>False</server>
        </pyqgis_plugin>
    </plugins>
    """.strip()
    config = _get_config()
    context = {
        'name': config.get('general', 'name'),
        'version': config.get('general', 'version'),
        'description': config.get('general', 'description'),
        'about': config.get('general', 'about'),
        'qgis_minimum_version': config.get('general', 'qgisMinimumVersion'),
        'homepage': config.get('general', 'homepage'),
        'filename': zip_path.name,
        'icon': '../resources/icon.png',
        'author': config.get('general', 'author'),
        'download_url': f'{base_url}/repo/{zip_path.name}',
        'update_date': dt.datetime.now(tz=dt.timezone.utc),
        'experimental': config.get('general', 'experimental'),
        'deprecated': config.get('general', 'deprecated'),
        'tracker': config.get('general', 'tracker'),
        'repository': config.get('general', 'repository'),
        'tags': config.get('general', 'tags'),
    }
    contents = contents_template.format(**context)
    repo_index = repo_base_dir / 'plugins.xml'
    repo_index.write_text(contents, encoding='utf-8')
    checklists_response = generate_checklists_response()
    checklists_endpoint = LOCAL_ROOT_DIR / 'docs/checklists/checklists.json'
    checklists_endpoint.parent.mkdir(parents=True, exist_ok=True)
    checklists_endpoint.write_text(checklists_response, encoding='utf-8')
    shutil.rmtree(temp_dir)


@task
def generate_checklists_response() -> str:
    repo_checklists_dir = LOCAL_ROOT_DIR / 'downloadable_checklists'
    all_checklists = []
    for item in repo_checklists_dir.iterdir():
        if item.is_file() and item.suffix == '.json':
            # TODO: add a try block here
            checklist_definition = json.loads(item.read_text())
            all_checklists.append(checklist_definition)
    return json.dumps(all_checklists, indent=2)


@task
def generate_zip(temp_dir) -> Path:
    temp_contents_dir = temp_dir / SRC_NAME
    environment.temp_contents_dir = temp_contents_dir
    prepare_deployment()
    zip_path = temp_dir / f'{SRC_NAME}.zip'
    with zipfile.ZipFile(zip_path, 'w') as fh:
        _add_to_zip(temp_contents_dir, fh, arc_path_base=temp_dir)
    info(f'files are in {temp_dir}')
    return zip_path


@task
@no_help
def prepare_deployment():
    copy_source_files()
    copy_icon()
    compile_resources()
    generate_metadata()


@task
@no_help
def copy_icon(temp_contents_dir: Path):
    config = _get_config()
    icon_path = LOCAL_ROOT_DIR / 'resources' / config.get('general', 'icon')
    target_path = temp_contents_dir / icon_path.name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(icon_path, target_path)


@task
@no_help
def compile_resources(temp_contents_dir: Path):
    info(f'compile_resources locals: {locals()}')
    resources_path = LOCAL_ROOT_DIR / 'resources' / 'resources.qrc'
    target_path = temp_contents_dir / PACKAGE_NAME / 'resources.py'
    target_path.parent.mkdir(parents=True, exist_ok=True)
    info(f'compile_resources target_path: {target_path}')
    subprocess.run(shlex.split(f'pyrcc5 -o {target_path} {resources_path}'))


@task
@no_help
def generate_metadata(temp_contents_dir: Path):
    config = _get_config()
    target_path = temp_contents_dir / 'metadata.txt'
    target_path.parent.mkdir(parents=True, exist_ok=True)
    info(f'generate_metadata target_path: {target_path}')
    with target_path.open(mode='w') as fh:
        config.write(fh)


@task
@no_help
def copy_source_files(temp_contents_dir: Path):
    info(f'copy_source_files base_target_dir: {temp_contents_dir}')
    temp_contents_dir.mkdir(parents=True, exist_ok=True)
    for child in (LOCAL_ROOT_DIR / 'src' / SRC_NAME).iterdir():
        target_path = temp_contents_dir / child.name
        info(f'copy_source_files child: {child}')
        info(f'copy_source_files target_path: {target_path}')
        handler = shutil.copytree if child.is_dir() else shutil.copy
        handler(str(child.resolve()), str(target_path))


@task
@no_help
def _get_plugin_config():
    source_config = configparser.ConfigParser()
    source_config.read(str(LOCAL_ROOT_DIR / 'plugin_config.ini'))
    return source_config


@task
@no_help
def _get_qgis_root_dir() -> Path:
    source_config = _get_plugin_config()
    profile = source_config.get('dev', 'profile')
    return Path.home() / f'.local/share/QGIS/QGIS3/profiles/{profile}'



def _read_file(relative_path: str):
    path = LOCAL_ROOT_DIR / relative_path
    with path.open() as fh:
        return fh.read()


def _add_to_zip(directory: Path, zip_handler: zipfile.ZipFile, arc_path_base: Path):
    for item in directory.iterdir():
        if item.is_file():
            zip_handler.write(item,arcname=str(item.relative_to(arc_path_base)))
        else:
            _add_to_zip(item, zip_handler, arc_path_base)


def _get_config() -> configparser.ConfigParser:
    readme_contents = _read_file('README.md')
    source_config = _get_plugin_config()
    source_general = source_config['general']
    config = configparser.ConfigParser()
    config['general'] = {
        'name': SRC_NAME.replace('_', ' ').replace('-', ' ').capitalize(),
        'qgisMinimumVersion': source_general.get('qgisMinimumVersion', '3.10'),
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
    return config
