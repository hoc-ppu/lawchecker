import os
import shutil
from pathlib import Path

import py2app
from setuptools import setup


def tree(path: Path):
    for item in path.rglob('*'):
        if item.is_file():
            yield (str(item.parent), [str(item)])


if os.path.exists('build'):
    shutil.rmtree('build')

if os.path.exists('dist'):
    shutil.rmtree('dist')

ENTRY_POINT = ['src/lawchecker/main.py']

DATA_FILES = list(tree(Path('ui_bundle'))) + list(tree(Path('templates')))

if Path('.env').exists():
    # Some items are secret and included in the .env file.
    DATA_FILES.append(('', ['.env']))


print(f'{DATA_FILES=}')

OPTIONS = {
    'argv_emulation': False,
    'strip': True,
    'includes': ['WebKit', 'Foundation', 'webview'],
    'iconfile': 'icon/icon.icns',
    # The below makes the app respect the system appearance
    # setting (e.g. dark mode). Not sure if it's necessary.
    'plist': {'NSRequiresAquaSystemAppearance': False},
    'excludes': ['setuptools'],
}

setup(
    name='Lawchecker',
    app=ENTRY_POINT,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
