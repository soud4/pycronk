import pytest

from pycronk.core.errors import Cancelled
from pycronk.ui.workers import TaskRunner


@pytest.fixture
def runner(qapp):
    runner = TaskRunner()
    yield runner
    runner.wait(2000)


def test_finished_with_result_and_progress(qtbot, runner):
    progress: list[float] = []

    def job(report, _cancel):
        report(1, 4)
        report(4, 4)
        return 42

    task = runner.start(job)
    task.signals.progress.connect(progress.append)
    with qtbot.waitSignal(task.signals.finished) as blocker:
        pass
    assert blocker.args == [42]
    qtbot.waitUntil(lambda: progress == [0.25, 1.0])


def test_progress_with_zero_total_is_complete(qtbot, runner):
    progress: list[float] = []
    task = runner.start(lambda report, _c: report(0, 0))
    task.signals.progress.connect(progress.append)
    qtbot.waitUntil(lambda: progress == [1.0])


def test_failure_is_reported(qtbot, runner):
    def job(_report, _cancel):
        raise ValueError("boom")

    task = runner.start(job)
    with qtbot.waitSignal(task.signals.failed) as blocker:
        pass
    assert isinstance(blocker.args[0], ValueError)


def test_cancellation(qtbot, runner):
    def job(_report, cancel):
        while not cancel.is_cancelled():
            pass
        raise Cancelled()

    task = runner.start(job)
    with qtbot.waitSignal(task.signals.cancelled):
        task.cancel()
