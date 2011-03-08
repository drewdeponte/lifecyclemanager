from setuptools import setup

PACKAGE = 'UserLog'
VERSION = '0.1'

setup(name=PACKAGE,
    version=VERSION,
    packages=['userlog'],
    entry_points={'trac.plugins': 'UserLog = userlog'},
    package_data={'userlog': ['templates/*.cs',
                                'htdocs/images/*.jpg',
                                'htdocs/css/*.css',
                                'htdocs/docs/*.css']},
)
