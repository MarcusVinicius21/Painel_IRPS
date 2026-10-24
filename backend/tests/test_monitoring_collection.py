from datetime import date
import pytest
from app.monitoring_collection import windows

def test_twelve_closed_months_plus_current_without_future_days():
    rows=windows(date(2026,10,24))
    assert len(rows)==13 and rows[0]==(date(2025,10,1),date(2025,10,31))
    assert rows[-2]==(date(2026,9,1),date(2026,9,30))
    assert rows[-1]==(date(2026,10,1),date(2026,10,24))
    assert len({r[0] for r in rows})==13

def test_window_crosses_leap_year_and_january():
    rows=windows(date(2024,1,1));assert rows[0][0]==date(2023,1,1)
    assert rows[-1]==(date(2024,1,1),date(2024,1,1))
    assert windows(date(2024,3,1))[-2][1]==date(2024,2,29)
