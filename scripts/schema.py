"""Allowed values, labels, and definitions shared by the validator and the site build.

Change an allowed value here and both the validator and the Methodology page follow.
"""

AGENCIES = {
    # name used in YAML: (url slug, display name).
    # Listed in descending annual ridership, FY 2024-25 (Phase 1 report; figures in site/config.json →
    # agency_ridership). The site shows agencies in this order.
    "SFMTA": ("sfmta", "Muni (SFMTA)"),
    "BART": ("bart", "BART"),
    "AC Transit": ("ac-transit", "AC Transit"),
    "Caltrain": ("caltrain", "Caltrain"),
}

PHASES = {
    1: "Phase 1",
    2: "Phase 2",
    "implementation_plan": "Implementation plan",
}

CATEGORIES = [
    "labor/overtime",
    "service planning",
    "procurement",
    "energy",
    "real estate",
    "capital",
    "revenue",
    "ridership/customer experience",
    "other",
]

# Order here is the column order on the scorecard. None = no primary source found yet.
STATUSES = {
    None: {
        "label": "Unverified",
        "glyph": "?",
        "definition": "No primary source has been found that establishes this entry's status. "
        "The tracker makes no claim about it until one is found.",
    },
    "not_adopted": {
        "label": "Not adopted",
        "glyph": "–",
        "definition": "The agency's governing board took the action required for this phase "
        "and did not include this recommendation. SB 63 lets each agency choose which "
        "Phase 1 strategies it commits to (Gov. Code §67766(b)), so this is a recorded "
        "choice, not a missed deadline.",
    },
    "not_started": {
        "label": "Not started",
        "glyph": "○",
        "definition": "The agency committed to the recommendation, and a primary source states "
        "that work has not begun.",
    },
    "adopted": {
        "label": "Adopted",
        "glyph": "◐",
        "definition": "The agency's governing board formally adopted the recommendation as a "
        "policy or budget action. Adoption is a commitment; it does not mean the work is done.",
    },
    "in_progress": {
        "label": "In progress",
        "glyph": "◑",
        "definition": "A primary source documents that work has begun (for example, a study "
        "has been contracted, a pilot has launched, or a rate change has been approved but "
        "not fully rolled out) and is not complete.",
    },
    "implemented": {
        "label": "Implemented",
        "glyph": "●",
        "definition": "A primary source documents that the recommended action is complete: a "
        "recommended study has been delivered to the board, or a recommended policy, price, "
        "or operating change is in effect.",
    },
    "missed": {
        "label": "Missed",
        "glyph": "✕",
        "definition": "A deadline that applies to the entry (statutory, or a completion date "
        "the agency or MTC set) has passed, and no primary source documents that the required "
        "action was taken.",
    },
    "superseded": {
        "label": "Superseded",
        "glyph": "↷",
        "definition": "A later formal action replaced this commitment, for example by folding "
        "it into an adopted Phase 2 implementation plan. The notes name the replacing action.",
    },
}

SOURCE_TYPES = {
    "statute": "Statute",
    "report": "Review report",
    "board_item": "Board item",
    "news_release": "News release",
    "agency_document": "Agency document",
}

MILESTONE_RESPONSIBLE = ["MTC", "oversight committee", "operators", "voters", "county elections officials"]

# What a recommendation commits the agency to do, classified only from wording, never from judgment about
# intent. Source of the wording (action_type_source):
#   adopted: the board's adoption document restates the strategy with an instruction (adopted_wording
#            quotes it). This is the commitment the board voted for, so it decides.
#   report:  the board adopted the strategy by reference or by heading only, or didn't adopt it; the
#            report's wording (recommendation) decides.
# action_type_basis quotes the deciding words; the validator checks they appear in that wording. An item's
# instruction decides it, not its title. Where wording has both a study verb and an action verb ("examine
# schedules and adjust"), the action decides it.
ACTION_TYPE_SOURCES = {
    "adopted": "the board's adopted wording",
    "report": "the report's wording",
}
ACTION_TYPES = {
    "action": {
        "label": "Direct action",
        "definition": "The agency changes its own prices, service, contracts, practices, or programs "
        "(for example: increase, earn, run, extend, offer, continue, adjust, carry out).",
    },
    "study": {
        "label": "Study or plan",
        "definition": "The agency produces an analysis or a plan without committing to a change "
        "(for example: study, identify, examine, explore, review, develop a vision or plan).",
    },
    "advocacy": {
        "label": "Ask another government",
        "definition": "The agency asks another body, such as the state, to act (for example: seek a deferral).",
    },
}

COMMITMENT_FIELDS = [
    "id", "agency", "phase", "recommendation", "category", "action_type", "action_type_basis",
    "action_type_source", "adopted_wording",
    "estimated_savings_usd", "savings_basis", "required_by",
    "target_completion", "target_completion_basis",
    "board_action", "status", "status_as_of", "sources", "notes",
]
OPTIONAL_FIELDS = {"target_completion", "target_completion_basis"}


# data/oversight.yaml
OVERSIGHT_KINDS = {"member", "meeting", "finding"}
IOC_SEATS = {
    "mtc_chair": "MTC chair or designee (§67764(a))",
    "operator_board": "Board member of a reviewed agency (§67764(b))",
    "expert": "Independent expert appointed by MTC (§67764(c))",
    "ex_officio": "State ex officio, non-voting (§67764(d))",
}
FINDING_BASES = {
    "service_or_safety": "Unacceptable impact on transit service or safety",
    "local_policy": "Inconsistent with other documented local policies and procedures",
}
OVERSIGHT_FIELDS = {
    "member": ["id", "kind", "name", "committee_role", "seat", "voting", "public_role", "board_agency",
               "status_as_of", "sources", "notes"],
    "meeting": ["id", "kind", "date", "title", "actions", "vote_record", "status_as_of", "sources", "notes"],
    "finding": ["id", "kind", "agency", "recommendation", "adopted_on", "basis", "expires_on", "renewed_on",
                "notice_to_legislature_on", "status_as_of", "sources", "notes"],
}
