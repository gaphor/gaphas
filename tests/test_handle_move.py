import pytest

from gaphas.handlemove import ItemHandleMove


@pytest.mark.asyncio
async def test_can_connect(line, box, connections, view):
    handle_move = ItemHandleMove(line, line.head, view)
    handle_move.connect((0, 0))

    assert connections.get_connection(line.head)


@pytest.mark.asyncio
async def test_handle_is_connected_and_constraint_removed_when_moved(
    line, box, connections, view
):
    handle_move = ItemHandleMove(line, line.head, view)
    handle_move.connect((0, 0))

    handle_move.start_move((0, 0))

    cinfo = connections.get_connection(line.head)
    constraint = cinfo.constraint
    assert constraint not in connections.solver.constraints


@pytest.mark.asyncio
async def test_connected_item_can_disconnect(line, box, connections, view):
    handle_move = ItemHandleMove(line, line.head, view)
    handle_move.connect((0, 0))

    cinfo = connections.get_connection(line.head)
    orig_constraint = cinfo.constraint

    handle_move.start_move((0, 0))
    handle_move.stop_move((100, 100))

    assert not connections.get_connection(line.head)
    assert orig_constraint not in connections.solver.constraints


@pytest.mark.asyncio
async def test_connected_item_can_reconnect(line, box, connections, view):
    handle_move = ItemHandleMove(line, line.head, view)
    handle_move.connect((0, 0))

    cinfo = connections.get_connection(line.head)
    orig_constraint = cinfo.constraint

    handle_move.start_move((0, 0))
    handle_move.stop_move((0, 0))

    cinfo = connections.get_connection(line.head)
    new_constraint = cinfo.constraint

    assert orig_constraint is not new_constraint
