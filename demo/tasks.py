from demo.models import CaseInput


CASES = [
    CaseInput(
        case_id="clear_deny_01",
        title="Late refund, no exception",
        customer_tier="standard",
        days_since_purchase=45,
        item_damaged=False,
        used_item=False,
        prior_refunds=0,
        explicit_exception=False,
        notes="Customer requests refund after policy window.",
        expected_decision="deny",
    ),
    CaseInput(
        case_id="clear_approve_01",
        title="Damaged item inside window",
        customer_tier="standard",
        days_since_purchase=12,
        item_damaged=True,
        used_item=False,
        prior_refunds=0,
        explicit_exception=False,
        notes="Item arrived damaged and request is within window.",
        expected_decision="approve",
    ),
    CaseInput(
        case_id="exception_01",
        title="Explicit exception granted by policy note",
        customer_tier="premium",
        days_since_purchase=42,
        item_damaged=False,
        used_item=False,
        prior_refunds=0,
        explicit_exception=True,
        notes="Premium support note allows override for this case.",
        expected_decision="approve",
    ),
    CaseInput(
        case_id="edge_deny_01",
        title="Used item outside allowed return condition",
        customer_tier="standard",
        days_since_purchase=18,
        item_damaged=False,
        used_item=True,
        prior_refunds=1,
        explicit_exception=False,
        notes="Within time window, but item was used and policy excludes it.",
        expected_decision="deny",
    ),
    CaseInput(
        case_id="borderline_01",
        title="Borderline case with conflicting signals",
        customer_tier="premium",
        days_since_purchase=31,
        item_damaged=True,
        used_item=False,
        prior_refunds=2,
        explicit_exception=False,
        notes="Slightly outside policy window, damaged item, premium customer.",
        expected_decision="escalate",
    ),
]


def get_cases():
    return CASES
