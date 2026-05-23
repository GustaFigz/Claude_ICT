from datetime import datetime, timedelta, timezone

from data_pipeline.schemas import Candle

_BASE = datetime(2026, 5, 26, 0, 0, tzinfo=timezone.utc)


def c(i: int, o: float, h: float, low: float, cl: float) -> Candle:
    return Candle(time=_BASE + timedelta(hours=i), open=o, high=h, low=low, close=cl, volume=100)
