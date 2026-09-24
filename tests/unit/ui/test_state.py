from pycronk.core.trace import Trace
from pycronk.services.models import Operation
from pycronk.services.settings import Settings, Theme
from pycronk.ui.state import Navigator, SettingsStore, TraceSnapshot, TraceStore


class MemorySettings:
    def __init__(self) -> None:
        self.saved: list[Settings] = []

    def load(self) -> Settings:
        return Settings()

    def save(self, settings: Settings) -> None:
        self.saved.append(settings)


def test_settings_store_saves_and_emits(qtbot):
    repo = MemorySettings()
    store = SettingsStore(repo)
    with qtbot.waitSignal(store.changed) as blocker:
        store.update(theme=Theme.DARK)
    assert store.current.theme is Theme.DARK
    assert blocker.args == [store.current]
    assert repo.saved == [store.current]


def test_settings_store_ignores_no_op(qtbot):
    repo = MemorySettings()
    store = SettingsStore(repo)
    with qtbot.assertNotEmitted(store.changed):
        store.update(theme=Theme.SYSTEM)
    assert repo.saved == []


def test_trace_store_publishes(qtbot):
    store = TraceStore()
    snapshot = TraceSnapshot(Operation.ENCRYPT, Trace(), "a", "b")
    with qtbot.waitSignal(store.changed) as blocker:
        store.publish(snapshot)
    assert store.latest is snapshot
    assert blocker.args == [snapshot]


def test_navigator(qtbot):
    navigator = Navigator()
    with qtbot.waitSignal(navigator.requested) as blocker:
        navigator.go("process")
    assert blocker.args == ["process"]
