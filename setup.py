"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-admin-toolbox',

    use_scm_version=True,

    description='Django admin toolbox - bunch of improvements for default django admin',
    long_description=long_description,
    long_description_content_type="text/x-rst",

    url='https://github.com/gbdlin/django-admin-toolbox',

    author='GwynBleidD',
    author_email='gbd.lin@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Environment :: Web Environment',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: User Interfaces',

        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',

        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='django admin toolbox sidebar tools improvements',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    python_requires=">=2.7, !=3.0*, !=3.1.*, !=3.2.*, !=3.3.*, <4",

    install_requires=[
        # 'django>=1.10,<1.11.9999',
        'six',
    ],

    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    setup_requires=[
        'setuptools_scm',
    ],

    include_package_data=True,

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'sample': ['package_data.dat'],
    # },

    # data_files=[('my_data', ['data/data_file'])],

    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)
