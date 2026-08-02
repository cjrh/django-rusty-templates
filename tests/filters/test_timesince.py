from datetime import date, datetime, timedelta

import pytest
import time_machine
from django.utils import timezone


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ value|timesince:now }}",
            {"value": datetime(2005, 12, 29), "now": datetime(2005, 12, 30)},
            "1\xa0day",
            id="explicit_datetime_argument",
        ),
        pytest.param(
            "{{ value|timesince:now }}",
            {
                "value": datetime(2018, 5, 9),
                "now": datetime(2018, 5, 9) + timedelta(days=365 + 364),
            },
            "1\xa0year, 11\xa0months",
            id="years_and_months",
        ),
        pytest.param(
            "{{ value|timesince:now }}",
            {"value": date(2024, 1, 1), "now": date(2024, 1, 2)},
            "1\xa0day",
            id="date_values",
        ),
        pytest.param(
            "{{ value|timesince:now }}",
            {
                "value": datetime(2024, 1, 1, tzinfo=timezone.get_fixed_timezone(0)),
                "now": datetime(2024, 1, 1, 8, tzinfo=timezone.get_fixed_timezone(0)),
            },
            "8\xa0hours",
            id="aware_datetimes",
        ),
        pytest.param(
            "{{ value|timesince:now }}",
            {
                "value": datetime(2024, 1, 1),
                "now": datetime(2024, 1, 1, tzinfo=timezone.get_fixed_timezone(0)),
            },
            "",
            id="naive_and_aware_datetimes",
        ),
        pytest.param("{{ value|timesince }}", {"value": None}, "", id="none_value"),
        pytest.param("{{ value|timesince }}", {"value": False}, "", id="false_value"),
        pytest.param("{{ missing|timesince }}", {}, "", id="missing_value"),
    ],
)
def test_timesince(assert_render, template, context, expected):
    assert_render(template, context, expected)


@time_machine.travel(datetime(2024, 1, 2, 12, 0), tick=False)
def test_timesince_without_argument_uses_current_time(assert_render):
    assert_render(
        "{{ value|timesince }}",
        {"value": datetime(2024, 1, 1, 10, 35)},
        "1\xa0day, 1\xa0hour",
    )
