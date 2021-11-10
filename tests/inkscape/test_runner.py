import errno
import logging
import os
from subprocess import CalledProcessError
import sys
import threading
import time

import pytest

from barnhunt.inkscape.runner import (
    Inkscape,
    RunInkscape,
    ShellModeInkscape,
    logging_output,
    )


class TestRunInkscape:
    def test_success(self):
        RunInkscape(executable='/bin/true')([])

    def test_failure(self, caplog):
        with pytest.raises(CalledProcessError):
            RunInkscape(executable='/bin/false')([])
        assert len(caplog.records) == 0

    def test_logs_output(self, caplog):
        RunInkscape(executable='/bin/echo')(['foo'])
        assert 'foo' in caplog.text

    def test_close(self):
        RunInkscape().close()


def test_logging_output(caplog):
    with logging_output('foo') as logfile:
        logfile.write(b'bar')
    assert len(caplog.records) == 1
    assert 'foo' in caplog.text
    assert 'bar' in caplog.text


class TestShellModeInkscape:
    @pytest.fixture
    def inkscape(self):
        return self._make_dummy()

    def _make_dummy(self):
        here = os.path.dirname(os.path.abspath(__file__))
        dummy = os.path.join(here, 'dummy_inkscape.py')
        return ShellModeInkscape(executable=sys.executable,
                                 inkscape_args=[dummy],
                                 timeout=3)

    def test_success(self, inkscape, caplog):
        inkscape(['true'])
        assert not any(r.levelno >= logging.INFO for r in caplog.records)

    def test_logs_output(self, inkscape, caplog):
        inkscape(['echo', 'foo'])
        assert any(r.levelno >= logging.INFO for r in caplog.records)
        assert 'foo' in caplog.text

    def test_close(self, inkscape):
        inkscape(['true'])
        pid = inkscape.pid
        assert pid is not None
        os.kill(pid, 0)

        inkscape.close()
        assert inkscape.child is None

        # check that child is killed within a reasonable time
        with pytest.raises(OSError) as excinfo:
            os.kill(pid, 0)
            for _ in range(10):
                time.sleep(0.05)
                os.kill(pid, 0)
        assert excinfo.value.errno == errno.ESRCH

    def test_thread_safe(self, inkscape, caplog):
        nthreads = 16
        pids = set()

        def target():
            inkscape(['true'])
            pids.add(inkscape.pid)

        run_in_threads(target, nthreads=nthreads)
        assert not any(r.levelno >= logging.INFO for r in caplog.records)
        assert len(pids) == nthreads


def run_in_threads(target, args=(), nthreads=16):
    threads = [threading.Thread(target=target, args=args)
               for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


class TestInkscape:
    @pytest.fixture
    def runner(self):
        return DummyInkscapeRunner()

    @pytest.fixture
    def tree(self):
        class DummyTree:
            def write(self, outfp, xml_declaration=False):
                pass
        return DummyTree()

    @pytest.fixture
    def inkscape(self, runner):
        rv = Inkscape()
        rv.run_inkscape = runner
        return rv

    def test_export_pdf(self, inkscape, runner, tree, tmp_path):
        output_path = tmp_path.joinpath('foo/bar.pdf').__fspath__()
        inkscape.export_pdf(tree, output_path)
        assert len(runner.commands) == 1
        args = runner.commands[0]
        assert args[1] == '--export-area-page'
        assert args[2] == f'--export-pdf={output_path}'
        assert tmp_path.joinpath('foo').is_dir()

    def test_contextmanager(self, inkscape, runner):
        with inkscape as rv:
            assert rv is inkscape
            assert not runner.closed
        assert runner.closed


class DummyInkscapeRunner:
    def __init__(self):
        self.commands = []
        self.closed = False

    def __call__(self, args):
        assert not self.closed
        self.commands.append(args)

    def close(self):
        self.closed = True
