import functools
import time
from typing import List

from gi.repository import GLib

from gaphas.decorators import g_async


@g_async()
def async_function(list, token):
    list.append(token)


@g_async(single=True)
def single_function(list, token):
    list.append(token)


@g_async(timeout=10)
def timeout_function(list, token):
    list.append(token)


def iteration():
    ctx = GLib.main_context_default()
    while ctx.pending():
        ctx.iteration(False)


def in_main_context(func):
    @functools.wraps(func)
    def run_async():
        GLib.idle_add(func)
        iteration()

    return run_async


@in_main_context
def test_in_main_context():
    assert GLib.main_depth() == 1


def test_function_is_called_when_not_in_main_loop():
    called: List[str] = []

    async_function(called, "called")

    assert "called" in called


@in_main_context
def test_function_is_not_called_directly_in_main_loop():
    called: List[str] = []

    async_function(called, "called")

    assert "called" not in called


def test_function_is_called_from_main_loop():
    called: List[str] = []

    @in_main_context
    def fn():
        async_function(called, "called")
        assert "called" not in called

    fn()

    assert "called" in called


def test_single_function_is_called_once():

    called: List[str] = []

    @in_main_context
    def fn():
        single_function(called, "first")
        single_function(called, "second")
        single_function(called, "third")

    fn()

    assert "first" in called
    assert "second" not in called
    assert "third" not in called


def test_timeout_function():

    called: List[str] = []

    @in_main_context
    def fn():
        timeout_function(called, "first")
        async_function(called, "second")

    fn()

    # wait a bit for timeout resource to trigger
    time.sleep(0.01)
    iteration()

    assert called == ["second", "first"]
