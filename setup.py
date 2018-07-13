"""
ML I/O
====================

**MLIO** is a toolkit for easy I/O operations on machine learning projects. It tries to solve the problem of
unified serialization framework as well as that of resource discovery and loading for local or remote storages.

MLIO is written on _Python >=3.6_
"""
import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('mlio/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open('requirements.txt', 'r') as fp:
    requirements = [x.strip() for x in fp.readlines()]

test_requirements = [
    'nose',
    'coverage~=4.3.4',
    'gensim~=2.3.0',
    'xgboost~=0.72',
]

setup(name='mlio',
      version=version,
      description='I/O for machine learning',
      long_description=__doc__,
      author='Konstantinos Paliouras',
      author_email='paliouras@workable.com',
      install_requires=requirements,
      tests_require=test_requirements,
      setup_requires=[
          'flake8',
          'nose'
      ],
      test_suite='nose.collector',
      extras_require={
          'test': test_requirements,
      },
      packages=[
          'mlio',
          'mlio.io',
          'mlio.io.context_dependencies',
          'mlio.io.serializers',
          'mlio.resources',
      ],
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent', 'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ]
      )
