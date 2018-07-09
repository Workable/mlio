import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('mlio/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open('requirements.txt', 'r') as fp:
    requirements = [x.strip() for x in fp.readlines()]

setup(name='mlio',
      version=version,
      description='I/O for machine learning',
      author='Konstantinos Paliouras',
      author_email='paliouras@workable.com',
      install_requires=requirements,
      tests_require=[
          'nose',
          'coverage~=4.3.4',
          'gensim~=2.3.0',
          'xgboost~=0.72',
      ],
      setup_requires=[
          'flake8',
          'nose'
      ],
      test_suite='nose.collector',
      packages=[
          'mlio',
          'mlio.io',
          'mlio.io.context_dependencies',
          'mlio.io.serializers',
          'mlio.resources',
      ],
      )