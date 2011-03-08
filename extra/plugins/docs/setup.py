from setuptools import setup

PACKAGE = 'Docs'
VERSION = '0.1'

setup(name=PACKAGE,
    version=VERSION,
    packages=['docs'],
    entry_points={'trac.plugins': 'Docs = docs'},
    package_data={'docs': ['templates/*.cs',
                                'htdocs/images/*.jpg',
                                'htdocs/css/*.css',
                                'htdocs/docs/*.css']},
)
