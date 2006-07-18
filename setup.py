
from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages

setup(
    name='gaphas',
    version='0.1.0',
    description='Gaphas is a GTK+ based diagramming widget',
    long_description="""\
Gaphas is a GTK+ based diagramming widget written in Python.
It is the logical successor of the DiaCanvas library.
""",

    classifiers=[
    'Development Status  ::  4 - Beta',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='',

    author="Arjan J. Molenaar",
    author_email='arjanmol@users.sourceforge.net',

    url='http://gaphor.sourceforge.net/',

    #download_url='http://cheeseshop.python.org/',

    license='GNU Library General Public License (LGPL, see COPYING)',

    packages=find_packages(exclude=['ez_setup']),

    install_requires=[
    'PyGTK >= 2.8.0',
    ],

    zip_safe=False,

    package_data={
    # -*- package_data: -*-
    },

    #test_suite = 'nose.collector',

    )
      
