from __future__ import annotations
import pandas as pd
import numpy as np
from dateutil import tz

def localize_series_to_tz(ts: pd.Series, tz_name: str) -> pd.Series:
    """Return a timezone-aware series localized to tz_name.
    - If values are timezone-aware: convert to tz_name
    - If values are naive: assume they are already in tz_name and localize
    """
    target = tz.gettz(tz_name)
    s = pd.to_datetime(ts, errors="coerce", utc=False)
    # If any tz-aware present, convert all to target (coerce to UTC then to target)
    if getattr(s.dt, "tz", None) is not None:
        return s.dt.tz_convert(target)
    # Otherwise localize as target
    return s.dt.tz_localize(target)
