import functools
import time
from typing import List

import pytest
from gi.repository import GLib

from gaphas.decorators import g_async


@g_async()
def async_function(self, token):
    self.append(token)


@g_async(single=True)
def single_function(list, token):
    list.append(token)


@g_async(timeout=10)
def timeout_function(list, token):
    list.append(token)


class Obj(list):
    @g_async(single=True)
    def single_method(self, token):
        self.append(token)


@pytest.fixture
def obj():
    return Obj()


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

    assert "first" not in called
    assert "second" not in called
    assert "third" in called


def test_single_method_is_called_once_per_instance():
    first = Obj()
    second = Obj()

    @in_main_context
    def fn():
        first.single_method("first")
        second.single_method("second")

    fn()

    assert "first" in first
    assert "second" in second
    assert "first" not in second
    assert "second" not in first


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
