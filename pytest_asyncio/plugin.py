"""pytest-asyncio implementation."""
import asyncio
import contextlib
import functools
import inspect
import socket

import pytest

try:
    from _pytest.python import transfer_markers
except ImportError:  # Pytest 4.1.0 removes the transfer_marker api (#104)

    def transfer_markers(*args, **kwargs):  # noqa
        """Noop when over pytest 4.1.0"""
        print(f"==== transfer_markers A")
        pass


from inspect import isasyncgenfunction


def _is_coroutine(obj):
    """Check to see if an object is really an asyncio coroutine."""
    print(f"==== _is_coroutine A")
    return asyncio.iscoroutinefunction(obj) or inspect.isgeneratorfunction(obj)


def pytest_configure(config):
    """Inject documentation."""
    config.addinivalue_line(
        "markers",
        "asyncio: "
        "mark the test as a coroutine, it will be "
        "run using an asyncio event loop",
    )


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    """A pytest hook to collect asyncio coroutines."""
    print(f"==== pytest_pycollect_makeitem A")
    if collector.funcnamefilter(name) and _is_coroutine(obj):
        print(f"==== pytest_pycollect_makeitem B")
        item = pytest.Function.from_parent(collector, name=name)
        print(f"==== pytest_pycollect_makeitem C")

        # Due to how pytest test collection works, module-level pytestmarks
        # are applied after the collection step. Since this is the collection
        # step, we look ourselves.
        print(f"==== pytest_pycollect_makeitem D")
        transfer_markers(obj, item.cls, item.module)
        print(f"==== pytest_pycollect_makeitem E")
        item = pytest.Function.from_parent(collector, name=name)  # To reload keywords.
        print(f"==== pytest_pycollect_makeitem F")

        if "asyncio" in item.keywords:
            print(f"==== pytest_pycollect_makeitem H")
            return list(collector._genfunctions(name, obj))
    print(f"==== pytest_pycollect_makeitem I")


class FixtureStripper:
    """Include additional Fixture, and then strip them"""

    REQUEST = "request"
    EVENT_LOOP = "event_loop"

    def __init__(self, fixturedef):
        print(f"==== FixtureStripper.__init__ A")
        self.fixturedef = fixturedef
        print(f"==== FixtureStripper.__init__ B")
        self.to_strip = set()
        print(f"==== FixtureStripper.__init__ C")

    def add(self, name):
        """Add fixture name to fixturedef
        and record in to_strip list (If not previously included)"""
        print(f"==== FixtureStripper.add A")
        if name in self.fixturedef.argnames:
            print(f"==== FixtureStripper.add B")
            return
        print(f"==== FixtureStripper.add C")
        self.fixturedef.argnames += (name,)
        print(f"==== FixtureStripper.add D")
        self.to_strip.add(name)
        print(f"==== FixtureStripper.add E")

    def get_and_strip_from(self, name, data_dict):
        """Strip name from data, and return value"""
        print(f"==== FixtureStripper.get_and_strip_from A")
        result = data_dict[name]
        print(f"==== FixtureStripper.get_and_strip_from B")
        if name in self.to_strip:
            print(f"==== FixtureStripper.get_and_strip_from D")
            del data_dict[name]
        print(f"==== FixtureStripper.get_and_strip_from E")
        return result


@pytest.hookimpl(trylast=True)
def pytest_fixture_post_finalizer(fixturedef, request):
    """Called after fixture teardown"""
    print(f"==== pytest_fixture_post_finalizer A")
    if fixturedef.argname == "event_loop":
        # Set empty loop policy, so that subsequent get_event_loop() provides a new loop
        print(f"==== pytest_fixture_post_finalizer B")
        asyncio.set_event_loop_policy(None)
    print(f"==== pytest_fixture_post_finalizer C")


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    """Adjust the event loop policy when an event loop is produced."""
    print(f"==== pytest_fixture_setup A")
    if fixturedef.argname == "event_loop":
        print(f"==== pytest_fixture_setup B")
        outcome = yield
        print(f"==== pytest_fixture_setup C")
        loop = outcome.get_result()
        print(f"==== pytest_fixture_setup D")
        policy = asyncio.get_event_loop_policy()
        print(f"==== pytest_fixture_setup E")
        try:
            old_loop = policy.get_event_loop()
            print(f"==== pytest_fixture_setup F")
            if old_loop is not loop:
                print(f"==== pytest_fixture_setup G")
                old_loop.close()
            print(f"==== pytest_fixture_setup H")
        except RuntimeError as e:
            # Swallow this, since it's probably bad event loop hygiene.
            print(f"==== pytest_fixture_setup I", e)
            pass
        print(f"==== pytest_fixture_setup J")
        policy.set_event_loop(loop)
        print(f"==== pytest_fixture_setup K")
        return

    print(f"==== pytest_fixture_setup L")
    if isasyncgenfunction(fixturedef.func):
        # This is an async generator function. Wrap it accordingly.
        print(f"==== pytest_fixture_setup M")
        generator = fixturedef.func
        print(f"==== pytest_fixture_setup N")

        fixture_stripper = FixtureStripper(fixturedef)
        print(f"==== pytest_fixture_setup O")
        fixture_stripper.add(FixtureStripper.EVENT_LOOP)
        print(f"==== pytest_fixture_setup P")
        fixture_stripper.add(FixtureStripper.REQUEST)
        print(f"==== pytest_fixture_setup Q")

        def wrapper(*args, **kwargs):
            print(f"==== pytest_fixture_setup wrapper 1 A")
            loop = fixture_stripper.get_and_strip_from(
                FixtureStripper.EVENT_LOOP, kwargs
            )
            print(f"==== pytest_fixture_setup wrapper 1 B")
            request = fixture_stripper.get_and_strip_from(
                FixtureStripper.REQUEST, kwargs
            )
            print(f"==== pytest_fixture_setup wrapper 1 C")

            gen_obj = generator(*args, **kwargs)
            print(f"==== pytest_fixture_setup wrapper 1 D")

            async def setup():
                print(f"==== pytest_fixture_setup wrapper 1 setup A")
                res = await gen_obj.__anext__()
                print(f"==== pytest_fixture_setup wrapper 1 setup B")
                return res

            print(f"==== pytest_fixture_setup wrapper 1 E")
            def finalizer():
                """Yield again, to finalize."""

                print(f"==== pytest_fixture_setup wrapper 1 finalizer A")
                async def async_finalizer():
                    print(f"==== pytest_fixture_setup wrapper 1 finalizer async_finalizer A")
                    try:
                        await gen_obj.__anext__()
                        print(f"==== pytest_fixture_setup wrapper 1 finalizer async_finalizer B")
                    except StopAsyncIteration:
                        print(f"==== pytest_fixture_setup wrapper 1 finalizer async_finalizer C")
                        pass
                    else:
                        print(f"==== pytest_fixture_setup wrapper 1 finalizer async_finalizer D")
                        msg = "Async generator fixture didn't stop."
                        msg += "Yield only once."
                        raise ValueError(msg)
                    print(f"==== pytest_fixture_setup wrapper 1 finalizer async_finalizer E")

                print(f"==== pytest_fixture_setup wrapper 1 finalizer B")
                loop.run_until_complete(async_finalizer())
                print(f"==== pytest_fixture_setup wrapper 1 finalizer C")

            print(f"==== pytest_fixture_setup wrapper 1 F")
            request.addfinalizer(finalizer)
            print(f"==== pytest_fixture_setup wrapper 1 G")
            x = loop.run_until_complete(setup())
            print(f"==== pytest_fixture_setup wrapper 1 H")
            return x

        print(f"==== pytest_fixture_setup R")
        fixturedef.func = wrapper
        print(f"==== pytest_fixture_setup S")
    elif inspect.iscoroutinefunction(fixturedef.func):
        print(f"==== pytest_fixture_setup T")
        coro = fixturedef.func
        print(f"==== pytest_fixture_setup U")

        fixture_stripper = FixtureStripper(fixturedef)
        print(f"==== pytest_fixture_setup V")
        fixture_stripper.add(FixtureStripper.EVENT_LOOP)
        print(f"==== pytest_fixture_setup W")

        def wrapper(*args, **kwargs):
            print(f"==== pytest_fixture_setup wrapper 2 A")
            loop = fixture_stripper.get_and_strip_from(
                FixtureStripper.EVENT_LOOP, kwargs
            )
            print(f"==== pytest_fixture_setup wrapper 2 B")

            async def setup():
                print(f"==== pytest_fixture_setup wrapper 2 setup A")
                res = await coro(*args, **kwargs)
                print(f"==== pytest_fixture_setup wrapper 2 setup B")
                return res

            print(f"==== pytest_fixture_setup wrapper 2 C")
            x = loop.run_until_complete(setup())
            print(f"==== pytest_fixture_setup wrapper 2 D")
            return x

        print(f"==== pytest_fixture_setup X")
        fixturedef.func = wrapper
    print(f"==== pytest_fixture_setup Y")
    yield
    print(f"==== pytest_fixture_setup Z")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    """
    Run asyncio marked test functions in an event loop instead of a normal
    function call.
    """
    print(f"==== pytest_pyfunc_call A")
    if "asyncio" in pyfuncitem.keywords:
        print(f"==== pytest_pyfunc_call B")
        if getattr(pyfuncitem.obj, "is_hypothesis_test", False):
            print(f"==== pytest_pyfunc_call C")
            pyfuncitem.obj.hypothesis.inner_test = wrap_in_sync(
                pyfuncitem.obj.hypothesis.inner_test,
                _loop=pyfuncitem.funcargs["event_loop"],
            )
            print(f"==== pytest_pyfunc_call D")
        else:
            print(f"==== pytest_pyfunc_call E")
            pyfuncitem.obj = wrap_in_sync(
                pyfuncitem.obj, _loop=pyfuncitem.funcargs["event_loop"]
            )
            print(f"==== pytest_pyfunc_call F")
    print(f"==== pytest_pyfunc_call G")
    yield
    print(f"==== pytest_pyfunc_call H")


def wrap_in_sync(func, _loop):
    """Return a sync wrapper around an async function executing it in the
    current event loop."""

    print(f"==== wrap_in_sync A")

    @functools.wraps(func)
    def inner(**kwargs):
        print(f"==== wrap_in_sync inner A")
        coro = func(**kwargs)
        print(f"==== wrap_in_sync inner B")
        if coro is not None:
            print(f"==== wrap_in_sync inner C")
            task = asyncio.ensure_future(coro, loop=_loop)
            print(f"==== wrap_in_sync inner D")
            try:
                print(f"==== wrap_in_sync inner E")
                _loop.run_until_complete(task)
                print(f"==== wrap_in_sync inner F")
            except BaseException:
                # run_until_complete doesn't get the result from exceptions
                # that are not subclasses of `Exception`. Consume all
                # exceptions to prevent asyncio's warning from logging.
                print(f"==== wrap_in_sync inner G")
                if task.done() and not task.cancelled():
                    print(f"==== wrap_in_sync inner H")
                    task.exception()
                    print(f"==== wrap_in_sync inner I")
                print(f"==== wrap_in_sync inner J")
                raise

    print(f"==== wrap_in_sync B")
    return inner


def pytest_runtest_setup(item):
    print(f"==== pytest_runtest_setup A")
    if "asyncio" in item.keywords:
        print(f"==== pytest_runtest_setup B")
        # inject an event loop fixture for all async tests
        if "event_loop" in item.fixturenames:
            print(f"==== pytest_runtest_setup C")
            item.fixturenames.remove("event_loop")
        print(f"==== pytest_runtest_setup D")
        item.fixturenames.insert(0, "event_loop")
    print(f"==== pytest_runtest_setup H")
    if (
        item.get_closest_marker("asyncio") is not None
        and not getattr(item.obj, "hypothesis", False)
        and getattr(item.obj, "is_hypothesis_test", False)
    ):
        print(f"==== pytest_runtest_setup I")
        pytest.fail(
            "test function `%r` is using Hypothesis, but pytest-asyncio "
            "only works with Hypothesis 3.64.0 or later." % item
        )
    print(f"==== pytest_runtest_setup J")


@pytest.fixture
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    print(f"==== event_loop A")
    loop = asyncio.get_event_loop_policy().new_event_loop()
    print(f"==== event_loop B")
    yield loop
    print(f"==== event_loop C")
    loop.close()
    print(f"==== event_loop D")


def _unused_tcp_port():
    """Find an unused localhost TCP port from 1024-65535 and return it."""
    print(f"==== _unused_tcp_port A")
    with contextlib.closing(socket.socket()) as sock:
        print(f"==== _unused_tcp_port B")
        sock.bind(("127.0.0.1", 0))
        print(f"==== _unused_tcp_port C")
        return sock.getsockname()[1]


@pytest.fixture
def unused_tcp_port():
    print(f"==== unused_tcp_port A")
    return _unused_tcp_port()


@pytest.fixture(scope="session")
def unused_tcp_port_factory():
    """A factory function, producing different unused TCP ports."""
    print(f"==== unused_tcp_port_factory A")
    produced = set()
    print(f"==== unused_tcp_port_factory B")

    def factory():
        """Return an unused port."""
        print(f"==== unused_tcp_port_factory factory A")
        port = _unused_tcp_port()
        print(f"==== unused_tcp_port_factory factory B")

        while port in produced:
            print(f"==== unused_tcp_port_factory factory C")
            port = _unused_tcp_port()
        print(f"==== unused_tcp_port_factory factory D")

        produced.add(port)
        print(f"==== unused_tcp_port_factory factory E")

        return port

    print(f"==== unused_tcp_port_factory C")
    return factory
