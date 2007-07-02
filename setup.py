
from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages
from distutils.cmd import Command

class build_doc(Command):
    description = 'Builds the documentation'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        epydoc_conf = 'epydoc.conf'

        try:
            import sys
            from epydoc import cli
            old_argv = sys.argv[1:]
            sys.argv[1:] = [
                '--config=%s' % epydoc_conf,
                '--no-private', # epydoc bug, not read from config
                '--simple-term',
                '--verbose'
            ]
            cli.cli()
            sys.argv[1:] = old_argv

        except ImportError:
            print 'epydoc not installed, skipping API documentation.'

setup(
    name='gaphas',
    version='0.2.0',
    description='Gaphas is a GTK+ based diagramming widget',
    long_description="""\
Gaphas is a GTK+ based diagramming widget written in Python.
It is the logical successor of the DiaCanvas library.

GTK+ and PyGTK is required.
""",

    classifiers=[
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='',

    author="Arjan J. Molenaar",
    author_email='arjanmol@users.sourceforge.net',

    url='http://gaphor.devjavu.com/wiki/Subprojects/Gaphas',

    #download_url='http://cheeseshop.python.org/',

    license='GNU Library General Public License (LGPL, see COPYING)',

    packages=find_packages(exclude=['ez_setup']),

    setup_requires = 'nose >= 0.9.2',

    install_requires=[
     'decorator >= 2.0.1',
#    'PyGTK >= 2.8.0',
    ],

    zip_safe=False,

    package_data={
    # -*- package_data: -*-
    },

    entry_points = {
    "distutils.commands": [ "nosetests = nose.commands:nosetests", ],
    },

    test_suite = 'nose.collector',

    cmdclass={'build_doc': build_doc },
    )
      
