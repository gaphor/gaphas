"""
Gaphas
======

Gaphor's Canvas.

This module contains the application independent parts of Gaphor's
Canvas.

Notes
=====

In py-cairo 1.8.0 (or 1.8.1, or 1.8.2) the multiplication order has
been reverted. This causes bugs in Gaphas.

Also a new method ``multiply()`` has been introduced. This method is
used in Gaphas instead of the multiplier (``*``). In both the
``Canvas`` and ``View`` class a workaround is provided in case an
older version of py-cairo is used.

Copyright notice
================

Copyright 2006, Arjan Molenaar & Dan Yeaw

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-FileCopyrightText: 2006 Arjan Molenaar & Dan Yeaw
SPDX-License-Identifer: Apache-2.0
"""
from gaphas.canvas import Canvas
from gaphas.connector import Handle
from gaphas.item import Element, Item, Line
