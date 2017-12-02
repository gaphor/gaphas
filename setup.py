#!/usr/bin/env python

# Copyright (C) 2006-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Dan Yeaw <dan@yeaw.me>
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
"""
Gaphas is a MVC item container that uses Toga for rendering. One of the nicer things
of this widget is that the user (model) is not bothered with bounding box
calculations: this is all done through Toga.

Some more features:

- Each item has it's own separate coordinate space (easy when items are
  rotated).
- Items on the item container can be connected to each other. Connections are
  maintained by a linear constraint solver.
- Multiple views on one ItemContainer.
- What is drawn is determined by Painters. Multiple painters can be used and
  painters can be chained.
- User interaction is handled by Tools. Tools can be chained.
- Versatile undo/redo system

.. _Cairo: http://cairographics.org/
.. _Toga: https://pybee.org/project/projects/libraries/toga/
"""

from setuptools import setup, find_packages

from ez_setup import use_setuptools

VERSION = '0.8.0'

use_setuptools()

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
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='',

    author="Dan Yeaw",
    author_email='dan@yeaw.me',

    url='https://gitlab.com/MBSE/gaphas',

    license='GNU Library General Public License (LGPL, see COPYING)',

    packages=find_packages(exclude=['ez_setup']),

    setup_requires=[
        'nose >= 0.10.4',
        'setuptools-git >= 0.3.4'
    ],

    install_requires=[
        'decorator >= 3.0.0',
        'simplegeneric >= 0.6',
        'toga >= 0.2.15'
    ],

    zip_safe=False,

    package_data={
        # -*- package_data: -*-
    },

    entry_points={
    },

    test_suite='nose.collector',
)
