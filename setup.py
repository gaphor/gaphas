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
from setuptools import setup


VERSION = "0.7.2"


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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="",
    author="Arjan J. Molenaar",
    author_email="arjanmol@users.sourceforge.net",
    url="http://gaphor.sourceforge.net",
    license="GNU Library General Public License (LGPL, see COPYING)",
    packages=[],
    setup_requires=["nose >= 0.10.4", "setuptools-git >= 0.3.4"],
    install_requires=[
        "decorator >= 3.0.0",
        "simplegeneric >= 0.6",
        "pycairo",
        "pygobject"
    ],
    python_requires=">=2.7",
    test_suite="nose.collector",
)
