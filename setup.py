from setuptools import setup

setup(setup_requires=['pbr'],
      pbr=True,
      entry_points={'pyang.plugin': ['yang-scan=scan:pyang_plugin_init']},
      scripts=['scan.py'])
