pytest-asyncio: pytest support for asyncio
==========================================

.. image:: https://img.shields.io/pypi/v/pytest-asyncio.svg
    :target: https://pypi.python.org/pypi/pytest-asyncio
.. image:: https://github.com/pytest-dev/pytest-asyncio/workflows/CI/badge.svg
    :target: https://github.com/pytest-dev/pytest-asyncio/actions?workflow=CI
.. image:: https://codecov.io/gh/pytest-dev/pytest-asyncio/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pytest-dev/pytest-asyncio
.. image:: https://img.shields.io/pypi/pyversions/pytest-asyncio.svg
    :target: https://github.com/pytest-dev/pytest-asyncio
    :alt: Supported Python versions
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

pytest-asyncio is an Apache2 licensed library, written in Python, for testing
asyncio code with pytest.

asyncio code is usually written in the form of coroutines, which makes it
slightly more difficult to test using normal testing tools. pytest-asyncio
provides useful fixtures and markers to make testing easier.

.. code-block:: python

    @pytest.mark.asyncio
    async def test_some_asyncio_code():
        res = await library.do_something()
        assert b'expected result' == res

pytest-asyncio has been strongly influenced by pytest-tornado_.

.. _pytest-tornado: https://github.com/eugeniy/pytest-tornado

Features
--------

- fixtures for creating and injecting versions of the asyncio event loop
- fixtures for injecting unused tcp ports
- pytest markers for treating tests as asyncio coroutines
- easy testing with non-default event loops
- support for `async def` fixtures and async generator fixtures

Installation
------------

To install pytest-asyncio, simply:

.. code-block:: bash

    $ pip install pytest-asyncio

This is enough for pytest to pick up pytest-asyncio.

Fixtures
--------

``event_loop``
~~~~~~~~~~~~~~
Creates and injects a new instance of the default asyncio event loop. By
default, the loop will be closed at the end of the test (i.e. the default
fixture scope is ``function``).

Note that just using the ``event_loop`` fixture won't make your test function
a coroutine. You'll need to interact with the event loop directly, using methods
like ``event_loop.run_until_complete``. See the ``pytest.mark.asyncio`` marker
for treating test functions like coroutines.

Simply using this fixture will not set the generated event loop as the
default asyncio event loop, or change the asyncio event loop policy in any way.
Use ``pytest.mark.asyncio`` for this purpose.

.. code-block:: python

    def test_http_client(event_loop):
        url = 'http://httpbin.org/get'
        resp = event_loop.run_until_complete(http_client(url))
        assert b'HTTP/1.1 200 OK' in resp

This fixture can be easily overridden in any of the standard pytest locations
(e.g. directly in the test file, or in ``conftest.py``) to use a non-default
event loop. This will take effect even if you're using the
``pytest.mark.asyncio`` marker and not the ``event_loop`` fixture directly.

.. code-block:: python

    @pytest.fixture
    def event_loop():
        loop = MyCustomLoop()
        yield loop
        loop.close()

If the ``pytest.mark.asyncio`` marker is applied, a pytest hook will
ensure the produced loop is set as the default global loop.
Fixtures depending on the ``event_loop`` fixture can expect the policy to be properly modified when they run.

``unused_tcp_port``
~~~~~~~~~~~~~~~~~~~
Finds and yields a single unused TCP port on the localhost interface. Useful for
binding temporary test servers.

``unused_tcp_port_factory``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
A callable which returns a different unused TCP port each invocation. Useful
when several unused TCP ports are required in a test.

.. code-block:: python

    def a_test(unused_tcp_port_factory):
        port1, port2 = unused_tcp_port_factory(), unused_tcp_port_factory()
        ...

Async fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Asynchronous fixtures are defined just like ordinary pytest fixtures, except they should be coroutines or asynchronous generators.

.. code-block:: python3

    @pytest.fixture
    async def async_gen_fixture():
        await asyncio.sleep(0.1)
        yield 'a value'

    @pytest.fixture(scope='module')
    async def async_fixture():
        return await asyncio.sleep(0.1)

All scopes are supported, but if you use a non-function scope you will need
to redefine the ``event_loop`` fixture to have the same or broader scope.
Async fixtures need the event loop, and so must have the same or narrower scope
than the ``event_loop`` fixture.


Markers
-------

``pytest.mark.asyncio``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Mark your test coroutine with this marker and pytest will execute it as an
asyncio task using the event loop provided by the ``event_loop`` fixture. See
the introductory section for an example.

The event loop used can be overridden by overriding the ``event_loop`` fixture
(see above).

In order to make your test code a little more concise, the pytest |pytestmark|_
feature can be used to mark entire modules or classes with this marker.
Only test coroutines will be affected (by default, coroutines prefixed by
``test_``), so, for example, fixtures are safe to define.

.. code-block:: python

    import asyncio
    import pytest

    # All test coroutines will be treated as marked.
    pytestmark = pytest.mark.asyncio

    async def test_example(event_loop):
        """No marker!"""
        await asyncio.sleep(0, loop=event_loop)

.. |pytestmark| replace:: ``pytestmark``
.. _pytestmark: http://doc.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules

Changelog
---------
0.16.0 (2021-10-16)
~~~~~~~~~~~~~~~~~~~
- Add support for Python 3.10

0.15.1 (2021-04-22)
~~~~~~~~~~~~~~~~~~~
- Hotfix for errors while closing event loops while replacing them.
  `#209 <https://github.com/pytest-dev/pytest-asyncio/issues/209>`_
  `#210 <https://github.com/pytest-dev/pytest-asyncio/issues/210>`_

0.15.0 (2021-04-19)
~~~~~~~~~~~~~~~~~~~
- Add support for Python 3.9
- Abandon support for Python 3.5. If you still require support for Python 3.5, please use pytest-asyncio v0.14 or earlier.
- Set ``unused_tcp_port_factory`` fixture scope to 'session'.
  `#163 <https://github.com/pytest-dev/pytest-asyncio/pull/163>`_
- Properly close event loops when replacing them.
  `#208 <https://github.com/pytest-dev/pytest-asyncio/issues/208>`_

0.14.0 (2020-06-24)
~~~~~~~~~~~~~~~~~~~
- Fix `#162 <https://github.com/pytest-dev/pytest-asyncio/issues/162>`_, and ``event_loop`` fixture behavior now is coherent on all scopes.
  `#164 <https://github.com/pytest-dev/pytest-asyncio/pull/164>`_

0.12.0 (2020-05-04)
~~~~~~~~~~~~~~~~~~~
- Run the event loop fixture as soon as possible. This helps with fixtures that have an implicit dependency on the event loop.
  `#156 <https://github.com/pytest-dev/pytest-asyncio/pull/156>`_

0.11.0 (2020-04-20)
~~~~~~~~~~~~~~~~~~~
- Test on 3.8, drop 3.3 and 3.4. Stick to 0.10 for these versions.
  `#152 <https://github.com/pytest-dev/pytest-asyncio/pull/152>`_
- Use the new Pytest 5.4.0 Function API. We therefore depend on pytest >= 5.4.0.
  `#142 <https://github.com/pytest-dev/pytest-asyncio/pull/142>`_
- Better ``pytest.skip`` support.
  `#126 <https://github.com/pytest-dev/pytest-asyncio/pull/126>`_

0.10.0 (2019-01-08)
~~~~~~~~~~~~~~~~~~~~
- ``pytest-asyncio`` integrates with `Hypothesis <https://hypothesis.readthedocs.io>`_
  to support ``@given`` on async test functions using ``asyncio``.
  `#102 <https://github.com/pytest-dev/pytest-asyncio/pull/102>`_
- Pytest 4.1 support.
  `#105 <https://github.com/pytest-dev/pytest-asyncio/pull/105>`_

0.9.0 (2018-07-28)
~~~~~~~~~~~~~~~~~~
- Python 3.7 support.
- Remove ``event_loop_process_pool`` fixture and
  ``pytest.mark.asyncio_process_pool`` marker (see
  https://bugs.python.org/issue34075 for deprecation and removal details)

0.8.0 (2017-09-23)
~~~~~~~~~~~~~~~~~~
- Improve integration with other packages (like aiohttp) with more careful event loop handling.
  `#64 <https://github.com/pytest-dev/pytest-asyncio/pull/64>`_

0.7.0 (2017-09-08)
~~~~~~~~~~~~~~~~~~
- Python versions pre-3.6 can use the async_generator library for async fixtures.
  `#62 <https://github.com/pytest-dev/pytest-asyncio/pull/62>`


0.6.0 (2017-05-28)
~~~~~~~~~~~~~~~~~~
- Support for Python versions pre-3.5 has been dropped.
- ``pytestmark`` now works on both module and class level.
- The ``forbid_global_loop`` parameter has been removed.
- Support for async and async gen fixtures has been added.
  `#45 <https://github.com/pytest-dev/pytest-asyncio/pull/45>`_
- The deprecation warning regarding ``asyncio.async()`` has been fixed.
  `#51 <https://github.com/pytest-dev/pytest-asyncio/pull/51>`_

0.5.0 (2016-09-07)
~~~~~~~~~~~~~~~~~~
- Introduced a changelog.
  `#31 <https://github.com/pytest-dev/pytest-asyncio/issues/31>`_
- The ``event_loop`` fixture is again responsible for closing itself.
  This makes the fixture slightly harder to correctly override, but enables
  other fixtures to depend on it correctly.
  `#30 <https://github.com/pytest-dev/pytest-asyncio/issues/30>`_
- Deal with the event loop policy by wrapping a special pytest hook,
  ``pytest_fixture_setup``. This allows setting the policy before fixtures
  dependent on the ``event_loop`` fixture run, thus allowing them to take
  advantage of the ``forbid_global_loop`` parameter. As a consequence of this,
  we now depend on pytest 3.0.
  `#29 <https://github.com/pytest-dev/pytest-asyncio/issues/29>`_


0.4.1 (2016-06-01)
~~~~~~~~~~~~~~~~~~
- Fix a bug preventing the propagation of exceptions from the plugin.
  `#25 <https://github.com/pytest-dev/pytest-asyncio/issues/25>`_

0.4.0 (2016-05-30)
~~~~~~~~~~~~~~~~~~
- Make ``event_loop`` fixtures simpler to override by closing them in the
  plugin, instead of directly in the fixture.
  `#21 <https://github.com/pytest-dev/pytest-asyncio/pull/21>`_
- Introduce the ``forbid_global_loop`` parameter.
  `#21 <https://github.com/pytest-dev/pytest-asyncio/pull/21>`_

0.3.0 (2015-12-19)
~~~~~~~~~~~~~~~~~~
- Support for Python 3.5 ``async``/``await`` syntax.
  `#17 <https://github.com/pytest-dev/pytest-asyncio/pull/17>`_

0.2.0 (2015-08-01)
~~~~~~~~~~~~~~~~~~
- ``unused_tcp_port_factory`` fixture.
  `#10 <https://github.com/pytest-dev/pytest-asyncio/issues/10>`_


0.1.1 (2015-04-23)
~~~~~~~~~~~~~~~~~~
Initial release.


Contributing
------------
Contributions are very welcome. Tests can be run with ``tox``, please ensure
the coverage at least stays the same before you submit a pull request.
