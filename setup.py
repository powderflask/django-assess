import sys, os, re

from setuptools import setup, Command, find_packages
from setuptools.command.test import test

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./*.pyc ./*.egg-info')


def run_tests(*args):
    from assessment.tests import run_tests
    errors = run_tests()
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)


test.run_tests = run_tests

NAME = "django-assess"

# get version without importing
with open("assessment/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode()).group(1))

# pull requirements
with open('requirements.txt', "r") as f:
    INSTALL_REQUIREMENTS = f.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(include=['assessment', 'assessment.*']),
    python_requires='>=3.5, <4',
    install_requires = INSTALL_REQUIREMENTS + [
        'setuptools-git',    # apparently needed to handle include_package_data from git repo?
    ],
    license="MIT",
    include_package_data=True,  # declarations in MANIFEST.in
    description=("Basic custom assessments as a reusable django app."),
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author="powderflask",
    author_email="powderflask@gmail.com",
    maintainer="powderflask",
    maintainer_email="powderflask@gmail.com",
    url="https://github.com/powderflask/django_assess",
    download_url="https://github.com/powderflask/django_assess/archive/v{}.tar.gz".format(VERSION),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
    cmdclass={
        'clean' : CleanCommand,
    },
    test_suite="dummy",
)

