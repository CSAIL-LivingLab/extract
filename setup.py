from setuptools import setup

setup(name='extract',
  version='0.9',
  description='field extraction from semi-structured textual data',
  long_description=open('README.md').read(),
  url='https://github.com/pcattori/extract',
  author='Pedro Cattori',
  author_email='pcattori@gmail.com',
  license='MIT',
  #classifiers=,
  #keywords=,
  packages=[
    'extract'
  ],
  install_requires=[
    'csv',
    'itertools',
    'numpy~>1.9.1',
    're',
    'scipy~>0.15.1'
  ],
  #package_data=,
  #data_files=,
  #scripts=,
  #entry_points=,
  #console_scripts=,
)
