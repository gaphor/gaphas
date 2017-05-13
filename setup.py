#!/usr/bin/env python

# Copyright (C) 2006-2011 Arjan Molenaar <gaphor@gmail.com>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.
"""\
Gaphas is a MVC canvas that uses Cairo_ for rendering. One of the nicer things
of this widget is that the user (model) is not bothered with bounding box
calculations: this is all done through Cairo.

Some more features:

- Each item has it's own separate coordinate space (easy when items are
  rotated).
- Items on the canvas can be connected to each other. Connections are
  maintained by a linear constraint solver.
- Multiple views on one Canvas.
- What is drawn is determined by Painters. Multiple painters can be used and
  painters can be chained.
- User interaction is handled by Tools. Tools can be chained.
- Versatile undo/redo system

GTK+ and PyGTK_ are required.

.. _Cairo: http://cairographics.org/
.. _PyGTK: http://www.pygtk.org/
"""

VERSION = '0.7.2'

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages
from distutils.cmd import Command

setup(
    name='gaphas',
    version=VERSION,
    description='Gaphas is a GTK+ based diagramming widget',
    long_description=__doc__,

    classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: GTK',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='',

    author="Arjan J. Molenaar",
    author_email='arjanmol@users.sourceforge.net',

    url='http://gaphor.sourceforge.net',

    #download_url='http://cheeseshop.python.org/',

    license='GNU Library General Public License (LGPL, see COPYING)',

    packages=find_packages(exclude=['ez_setup']),

    setup_requires = [
     'nose >= 0.10.4',
     'setuptools-git >= 0.3.4'
    ],

    install_requires=[
     'decorator >= 3.0.0',
     'simplegeneric >= 0.6',
#    'PyGTK >= 2.8.0',
#    'cairo >= 1.8.2'
    ],

    zip_safe=False,

    package_data={
    # -*- package_data: -*-
    },

    entry_points = {
    },

    test_suite = 'nose.collector',
    )
      
