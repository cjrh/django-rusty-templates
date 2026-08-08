"""
Adapted from
https://github.com/django/django/blob/5.2/tests/template_tests/filter_tests/test_join.py
"""

import pytest
from django.template import VariableDoesNotExist
from inline_snapshot import snapshot
from django.utils.functional import lazy
from django.utils.safestring import mark_safe


class HtmlValue:
    def __str__(self):
        return "<from-str&>"

    def __html__(self):
        return "<from-html&>"


class SafeStringFromStr:
    def __str__(self):
        return mark_safe("<from-safe-str&>")


class FailingJoiner(str):
    def join(self, values):
        raise TypeError("join failed")


class HtmlJoiner:
    def __html__(self):
        return FailingJoiner(",")


class JoinedHtml(str):
    def __html__(self):
        return "<joined-html&>"


class HtmlResultJoiner(str):
    def join(self, values):
        return JoinedHtml("from-str")


class HtmlResultSeparator:
    def __html__(self):
        return HtmlResultJoiner(",")


class BadHtmlReturnsInt:
    def __html__(self):
        return 1


class LaterStrRaisesValueError:
    def __str__(self):
        raise ValueError("boom")


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            '{{ a|join:", " }}',
            {"a": ["alpha", "beta & me"]},
            "alpha, beta &amp; me",
            id="autoescape_on",
        ),
        pytest.param(
            '{% autoescape off %}{{ a|join:", " }}{% endautoescape %}',
            {"a": ["alpha", "beta & me"]},
            "alpha, beta & me",
            id="autoescape_off",
        ),
        pytest.param(
            '{{ a|join:" &amp; " }}',
            {"a": ["alpha", "beta & me"]},
            "alpha &amp; beta &amp; me",
            id="literal_separator",
        ),
        pytest.param(
            '{% autoescape off %}{{ a|join:" &amp; " }}{% endautoescape %}',
            {"a": ["alpha", "beta & me"]},
            "alpha &amp; beta & me",
            id="literal_separator_autoescape_off",
        ),
        pytest.param(
            "{{ a|join:var }}",
            {"a": ["alpha", "beta & me"], "var": " & "},
            "alpha &amp; beta &amp; me",
            id="unsafe_separator",
        ),
        pytest.param(
            "{{ a|join:var }}",
            {"a": ["alpha", "beta & me"], "var": mark_safe(" & ")},
            "alpha & beta &amp; me",
            id="safe_separator",
        ),
        pytest.param(
            '{{ a|join:", " }}',
            {"a": ["<em>alpha</em>", mark_safe("<strong>beta</strong>")]},
            "&lt;em&gt;alpha&lt;/em&gt;, <strong>beta</strong>",
            id="safe_values",
        ),
        pytest.param(
            "{{ a|join:var|lower }}",
            {"a": ["Alpha", "Beta & me"], "var": " & "},
            "alpha &amp; beta &amp; me",
            id="unsafe_separator_chained",
        ),
        pytest.param(
            "{{ a|join:var|lower }}",
            {"a": ["Alpha", "Beta & me"], "var": mark_safe(" & ")},
            "alpha & beta &amp; me",
            id="safe_separator_chained",
        ),
        pytest.param(
            "{{ value|join:', ' }}",
            {"value": [0, 1, 2]},
            "0, 1, 2",
            id="coerces_values_to_strings",
        ),
        pytest.param(
            "{{ value|join:', ' }}",
            {"value": 123},
            "123",
            id="non_iterable",
        ),
        pytest.param(
            "{{ value|join:', ' }}",
            {},
            "",
            id="missing_variable",
        ),
    ],
)
def test_join(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_join_missing_argument(assert_parse_error):
    assert_parse_error(
        template="{{ value|join }}",
        django_message=snapshot("join requires 2 arguments, 1 provided"),
        rusty_message=snapshot("""\
  × Expected an argument
   ╭────
 1 │ {{ value|join }}
   ·          ──┬─
   ·            ╰── here
   ╰────
"""),
    )


def test_join_missing_argument_variable(template_engine):
    template = template_engine.from_string("{{ missing|join:arg }}")
    with pytest.raises(VariableDoesNotExist):
        template.render({})


@pytest.mark.parametrize(
    "context,expected",
    [
        pytest.param(
            {"values": [HtmlValue(), "end"], "separator": ", "},
            "<from-html&>, end",
            id="html_value",
        ),
        pytest.param(
            {"values": ["start", "end"], "separator": HtmlValue()},
            "start<from-html&>end",
            id="html_separator",
        ),
        pytest.param(
            {"values": [SafeStringFromStr(), "end"], "separator": ", "},
            "&lt;from-safe-str&amp;&gt;, end",
            id="safe_string_from_str",
        ),
    ],
)
def test_join_conditional_escaping(assert_render, context, expected):
    assert_render("{{ values|join:separator }}", context, expected)


def test_join_lazy_value(assert_render):
    value = lazy(lambda: "<from-lazy&>", str)()
    assert_render(
        "{{ values|join:', ' }}",
        {"values": [value, "end"]},
        "&lt;from-lazy&amp;&gt;, end",
    )


def test_join_html_separator_type_error(assert_render):
    assert_render(
        "{{ values|join:separator }}",
        {"values": ["a", "b"], "separator": HtmlJoiner()},
        "[&#x27;a&#x27;, &#x27;b&#x27;]",
    )


def test_join_html_separator_safe_result(assert_render):
    assert_render(
        "{{ values|join:separator }}",
        {"values": ["a", "b"], "separator": HtmlResultSeparator()},
        "<joined-html&>",
    )


def test_join_evaluates_all_values_before_join(template_engine):
    template = template_engine.from_string("{{ values|join:',' }}")
    with pytest.raises(ValueError, match="boom"):
        template.render({"values": [BadHtmlReturnsInt(), LaterStrRaisesValueError()]})


def test_join_autoescape_off_with_html(assert_render):
    template = "{% autoescape off %}{{ values|join:separator }}{% endautoescape %}"
    context = {
        "values": ["<p>Hello World!</p>", "beta & me", "<script>Hi!</script>"],
        "separator": "<br/>",
    }
    expected = "<p>Hello World!</p><br/>beta & me<br/><script>Hi!</script>"
    assert_render(template, context, expected)
