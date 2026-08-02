from datetime import date, datetime, time

import pytest
from django.template import VariableDoesNotExist
from django.test import override_settings
from django.utils import timezone, translation


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ value|time }}",
            {"value": time(16, 25)},
            "4:25 p.m.",
            id="default_format",
        ),
        pytest.param(
            '{{ value|time:"h" }}',
            {"value": time(13)},
            "01",
            id="custom_12_hour_format",
        ),
        pytest.param(
            '{{ value|time:"h" }}',
            {"value": time(0)},
            "12",
            id="midnight_12_hour_format",
        ),
        pytest.param(
            '{{ value|time:"P:e:O:T:Z" }}',
            {"value": time(4, tzinfo=timezone.get_fixed_timezone(30))},
            "4 a.m.::::",
            id="time_with_tzinfo",
        ),
        pytest.param(
            '{{ value|time:"P:e:O:T:Z" }}',
            {"value": date(2024, 1, 1)},
            "",
            id="date_is_not_a_time",
        ),
        pytest.param(
            "{{ value|time }}",
            {"value": "not-a-time"},
            "",
            id="invalid_value",
        ),
        pytest.param("{{ value|time }}", {"value": None}, "", id="none_value"),
        pytest.param("{{ missing|time }}", {}, "", id="missing_value"),
    ],
)
def test_time(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_time_is_localized(assert_render):
    with translation.override("fr"):
        assert_render("{{ value|time }}", {"value": time(16, 25)}, "16:25")


@override_settings(USE_TZ=True, TIME_ZONE="UTC")
def test_time_converts_aware_datetimes_to_the_active_timezone(assert_render):
    value = datetime(2024, 1, 1, 16, 25, tzinfo=timezone.get_fixed_timezone(0))
    with timezone.override("Asia/Kolkata"):
        assert_render('{{ value|time:"H:i e" }}', {"value": value}, "21:55 IST")


@pytest.mark.parametrize("filter_name", ["time", "timesince", "timeuntil"])
def test_missing_value_still_resolves_filter_argument(template_engine, filter_name):
    with pytest.raises(VariableDoesNotExist):
        template_engine.from_string(
            f"{{{{ missing|{filter_name}:also_missing }}}}"
        ).render({})


@override_settings(USE_TZ=True)
def test_time_annotates_localtime_errors(template_engine):
    class ExplodingDatetime(datetime):
        @property
        def convert_to_local_time(self):
            raise RuntimeError("localtime failed")

    value = ExplodingDatetime(2024, 1, 1, 12, tzinfo=timezone.get_fixed_timezone(0))
    with pytest.raises(RuntimeError, match="localtime failed"):
        template_engine.from_string("{{ value|time }}").render({"value": value})
