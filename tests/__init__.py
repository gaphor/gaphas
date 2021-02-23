import os

import gi

TEST_GTK_VERSION = os.getenv("TEST_GTK_VERSION", "4.0")

gi.require_version("Gdk", TEST_GTK_VERSION)
gi.require_version("Gtk", TEST_GTK_VERSION)
