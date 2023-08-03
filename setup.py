#!/usr/bin/env python3
# This file is a part of misk and is subject to the the terms of the MIT license.
# Copyright (c) Mark Gillard <mark.gillard@outlook.com.au>
# See https://github.com/marzer/misk/blob/master/LICENSE.txt for the full license text.
# SPDX-License-Identifier: MIT

# set up based on this: https://thucnc.medium.com/how-to-publish-your-own-python-package-to-pypi-4318868210f9
# windows:
# py setup.py sdist bdist_wheel && twine upload dist/* && rmdir /S /Q dist

import re

from setuptools import find_packages, setup

README = ''
with open(r'README.md', encoding=r'utf-8') as file:
	README = file.read()

CHANGELOG = ''
with open(r'CHANGELOG.md', encoding=r'utf-8') as file:
	CHANGELOG = f'\n\n{file.read()}\n\n'
CHANGELOG = re.sub(r'\n#+\s*Changelog\s*?\n', '\n## Changelog\n', CHANGELOG, flags=re.I).strip()

SETUP_ARGS = {
	r'name': r'misk',
	r'version': r'0.8.1',
	r'description': r'Miscellaneous useful bits for python 3.',
	r'long_description_content_type': r'text/markdown',
	r'long_description': f'{README}\n<br><br>\n{CHANGELOG}'.strip(),
	r'license': r'MIT',
	r'packages': find_packages(),
	r'author': r'Mark Gillard',
	r'author_email': r'mark.gillard@outlook.com.au',
	r'keywords': ['utilities'],  # ???
	r'url': r'https://github.com/marzer/misk',
	r'download_url': r'https://pypi.org/project/misk/',
	r'project_urls': {
	r'Source': r'https://github.com/marzer/misk',
	r'Tracker': r'https://github.com/marzer/misk/issues'
	},
	r'python_requires': r'>=3.7'
}

REQUIRES = None
with open(r'requirements.txt', encoding='utf-8') as file:
	REQUIRES = file.read().strip().split()

if __name__ == '__main__':
	setup(**SETUP_ARGS, install_requires=REQUIRES)
