import os
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Only the actively maintained part of the repository is installable:
# the language-vitality classifier in classification/ (Python 3).
# The legacy data-collection pipeline (ld/, parser_aggregator.py and the
# Django apps dld/ and ml/) is Python 2 code pinned to Django 1.11 and South;
# its historical requirements are documented in README.md and deliberately
# not declared here, so that installing this package never pulls in
# unsupported, vulnerable versions.
setup(
    name='langdeath',
    version='0.2',
    description='Digital Language Death.',
    author='Judit Acs',
    author_email='judit@sch.bme.hu',
    python_requires='>=3.9',
    # The classifier runs as scripts from classification/; installing this
    # package only provides its dependencies.
    packages=[],
    install_requires=[
        'numpy',
        'pandas',
        'scikit-learn',
    ],
)
