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

GTK+ and PyGObject_ are required.

.. _Cairo: http://cairographics.org/
.. _PyGObject: https://pygobject.readthedocs.io/
"""

import sys

from setuptools import setup, find_packages

VERSION = "1.0.0rc1"

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner = ["pytest-runner"] if needs_pytest else []
pytest_cov = ["pytest-cov"] if needs_pytest else []
setup(
    name="gaphas",
    version=VERSION,
    description="Gaphas is a GTK+ based diagramming widget",
    long_description=__doc__,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="",
    author="Arjan J. Molenaar",
    author_email="arjanmol@users.sourceforge.net",
    url="https://github.com/gaphor/gaphas",
    license="GNU Library General Public License (LGPL, see COPYING)",
    packages=find_packages(),
    setup_requires=["setuptools-git >= 0.3.4"] + pytest_runner + pytest_cov,
    install_requires=[
        "decorator >= 3.0.0",
        "simplegeneric >= 0.6",
        "PyGObject >= 3.20.0",
        "pycairo >= 1.10.0",
        "future >= 0.17.0",
    ],
    zip_safe=False,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    package_data={
        # -*- package_data: -*-
    },
    entry_points={},
    tests_require=["pytest"],
)
