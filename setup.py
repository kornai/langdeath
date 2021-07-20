import os
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='langdeath',
    version='0.1',
    description='Digital Language Death.',
    #url='http://www.example.com/',  #TODO
    author='Judit Acs',
    author_email='judit@sch.bme.hu',
    install_requires=[
        'django==1.11.18',
        'django-jsonfield',
        'Pillow==8.2.0' ,
        'South==0.8',
        'pandas==0.18.1',
        'numpy>=1.6.1',
        'scipy>=0.9',
        'sklearn'
    ]
)
