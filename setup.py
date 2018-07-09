#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from setuptools import setup

with open('requirements.txt', 'r') as fp:
    requirements = [x.strip() for x in fp.readlines()]

setup(name='mlio',
      version='1.0.0',
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
