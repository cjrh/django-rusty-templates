from datetime import date, datetime

import pytest
import time_machine
from django.utils import timezone


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ value|timeuntil:now }}",
            {"value": datetime(2005, 12, 30), "now": datetime(2005, 12, 29)},
            "1\xa0day",
            id="explicit_datetime_argument",
        ),
        pytest.param(
            "{{ value|timeuntil:now }}",
            {
                "value": datetime(2024, 1, 3, 6),
                "now": datetime(2024, 1, 1),
            },
            "2\xa0days, 6\xa0hours",
            id="days_and_hours",
        ),
        pytest.param(
            "{{ value|timeuntil:now }}",
            {"value": datetime(2024, 1, 1), "now": datetime(2024, 1, 2)},
            "0\xa0minutes",
            id="past_value",
        ),
        pytest.param(
            "{{ value|timeuntil:now }}",
            {"value": date(2024, 1, 2), "now": date(2024, 1, 1)},
            "1\xa0day",
            id="date_values",
        ),
        pytest.param(
            "{{ value|timeuntil:now }}",
            {
                "value": datetime(2024, 1, 1, tzinfo=timezone.get_fixed_timezone(0)),
                "now": datetime(2024, 1, 1, 8, tzinfo=timezone.get_fixed_timezone(0)),
            },
            "0\xa0minutes",
            id="aware_datetimes",
        ),
        pytest.param(
            "{{ value|timeuntil:now }}",
            {
                "value": datetime(2024, 1, 2),
                "now": datetime(2024, 1, 1, tzinfo=timezone.get_fixed_timezone(0)),
            },
            "",
            id="naive_and_aware_datetimes",
        ),
        pytest.param("{{ value|timeuntil }}", {"value": None}, "", id="none_value"),
        pytest.param("{{ value|timeuntil }}", {"value": False}, "", id="false_value"),
        pytest.param("{{ missing|timeuntil }}", {}, "", id="missing_value"),
    ],
)
def test_timeuntil(assert_render, template, context, expected):
    assert_render(template, context, expected)


@time_machine.travel(datetime(2024, 1, 1, 12, 0), tick=False)
def test_timeuntil_without_argument_uses_current_time(assert_render):
    assert_render(
        "{{ value|timeuntil }}",
        {"value": datetime(2024, 1, 2, 13, 0)},
        "1\xa0day, 1\xa0hour",
    )
