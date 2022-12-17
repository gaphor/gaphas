import gaphas


def test_gtk_dependency(archrule):
    archrule("GTK dependency").match("gaphas*").exclude(
        "gaphas.tool*", "gaphas.view*"
    ).should_not_import("gi.repository.Gdk", "gi.repository.Gtk").check(
        gaphas, skip_type_checking=True
    )
