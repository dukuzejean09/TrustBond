import inspect

from app.api.v1.hotspots import recompute_hotspots


def test_recompute_hotspots_no_background_tasks_argument() -> None:
    params = inspect.signature(recompute_hotspots).parameters

    assert "background_tasks" not in params
    assert inspect.iscoroutinefunction(recompute_hotspots)
