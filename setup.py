# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in chem_intercompany/__init__.py
from chem_intercompany import __version__ as version

setup(
	name='chem_intercompany',
	version=version,
	description='To manage inter company transactions for chemical',
	author='FinByz Tech Pvt. Ltd.',
	author_email='info@finbyz.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
