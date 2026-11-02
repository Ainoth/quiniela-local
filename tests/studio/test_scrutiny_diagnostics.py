"""Reports attribute a winning column only to saved, failing conditions."""

import pytest

from quiniela_ai_studio.domain.filters import BasicFilters
from quiniela_ai_studio.domain.reduction_rules import ReductionRule
from quiniela_ai_studio.domain.scrutiny_diagnostics import explain_filter_rejections


@pytest.mark.parametrize(
    ("tab", "kind", "sign", "allowed", "label"),
    (
        (0, "allowed_count", "X", (1,), "Cuenta"),
        (1, "allowed_run_length", "1", (4,), "SSeguidos"),
        (17, "allowed_count", "X", (1,), "FSSeguidos"),
        (18, "allowed_interruption_total", "", (1,), "Interrupciones"),
    ),
)
def test_rejection_report_names_the_reduction_and_actual_value(tab, kind, sign, allowed, label):
    rule = ReductionRule(
        f"diagnostic-{tab}", kind, 0, 14, sign=sign,
        allowed_values=allowed, tab_index=tab,
    )
    spec = BasicFilters(reduction_rules=(rule,), reduction_tabs_enabled=(tab,)).parameters()

    failures = explain_filter_rejections("1" * 14, spec)

    wanted = "valores " + ", ".join(map(str, allowed))
    rule_failure = next(failure for failure in failures if failure["expected"] == wanted)
    assert rule_failure["reduction"] == label
    expected_observed = "14" if kind == "allowed_run_length" else "0"
    assert rule_failure["observed"] == expected_observed
