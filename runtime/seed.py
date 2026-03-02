"""Seed mock Airtel dialog flows into MongoDB (idempotent)."""

from __future__ import annotations

import logging
from datetime import datetime

log = logging.getLogger("runtime.seed")

ORG_ID = "airtel_demo"
PROJECT_ID = "voice-bot"

# ---------------------------------------------------------------------------
# Helper to build a flow node
# ---------------------------------------------------------------------------

_counter = 0

def _nid():
    global _counter
    _counter += 1
    return f"vn_{_counter}"

def _pos(y: int, x: int = 250):
    return {"x": x, "y": y}

# ---------------------------------------------------------------------------
# Flow definitions
# ---------------------------------------------------------------------------

def _recharge_flow():
    n = [_nid() for _ in range(8)]
    return {
        "name": "Recharge Flow",
        "metadata": {"intent": "recharge"},
        "nodes": [
            {"id": n[0], "type": "start",        "data": {"type": "start",        "label": "Start"},                                                             "position": _pos(0)},
            {"id": n[1], "type": "message",       "data": {"type": "message",      "label": "Greet",       "message": "Sure, I'll help you with a recharge."},    "position": _pos(120)},
            {"id": n[2], "type": "entity",        "data": {"type": "entity",       "label": "Mobile No",   "entityName": "mobileNumber", "entityType": "phone", "prompt": "What mobile number would you like to recharge?"}, "position": _pos(260)},
            {"id": n[3], "type": "entity",        "data": {"type": "entity",       "label": "Amount",      "entityName": "amount", "entityType": "number", "prompt": "What amount would you like to recharge? (₹49 / ₹199 / ₹399 / ₹599)"}, "position": _pos(420)},
            {"id": n[4], "type": "confirmation",  "data": {"type": "confirmation", "label": "Confirm",     "question": "Recharge {{mobileNumber}} with ₹{{amount}}. Shall I proceed?", "yesLabel": "Yes", "noLabel": "No"}, "position": _pos(580)},
            {"id": n[5], "type": "tool",          "data": {"type": "tool",         "label": "Process",     "toolName": "processRecharge", "description": "Process the recharge via billing API"}, "position": _pos(740, 100)},
            {"id": n[6], "type": "message",       "data": {"type": "message",      "label": "Done",        "message": "Done! ₹{{amount}} has been recharged to {{mobileNumber}}. Thank you for calling Airtel!"}, "position": _pos(880, 100)},
            {"id": n[7], "type": "end",           "data": {"type": "end",          "label": "End"},                                                                "position": _pos(1020)},
        ],
        "edges": [
            {"id": f"e_{n[0]}_{n[1]}", "source": n[0], "target": n[1]},
            {"id": f"e_{n[1]}_{n[2]}", "source": n[1], "target": n[2]},
            {"id": f"e_{n[2]}_{n[3]}", "source": n[2], "target": n[3]},
            {"id": f"e_{n[3]}_{n[4]}", "source": n[3], "target": n[4]},
            {"id": f"e_{n[4]}_{n[5]}", "source": n[4], "target": n[5], "sourceHandle": "yes"},
            {"id": f"e_{n[4]}_{n[7]}", "source": n[4], "target": n[7], "sourceHandle": "no"},
            {"id": f"e_{n[5]}_{n[6]}", "source": n[5], "target": n[6]},
            {"id": f"e_{n[6]}_{n[7]}", "source": n[6], "target": n[7]},
        ],
    }


def _billing_flow():
    n = [_nid() for _ in range(8)]
    return {
        "name": "Billing Flow",
        "metadata": {"intent": "billing"},
        "nodes": [
            {"id": n[0], "type": "start",        "data": {"type": "start",        "label": "Start"},                                                                 "position": _pos(0)},
            {"id": n[1], "type": "message",       "data": {"type": "message",      "label": "Greet",       "message": "Let me help you with your billing query."},    "position": _pos(120)},
            {"id": n[2], "type": "entity",        "data": {"type": "entity",       "label": "Mobile No",   "entityName": "mobileNumber", "entityType": "phone", "prompt": "Please provide your registered mobile number."}, "position": _pos(260)},
            {"id": n[3], "type": "tool",          "data": {"type": "tool",         "label": "Fetch Bill",  "toolName": "fetchBill", "description": "Fetch current bill details"}, "position": _pos(400)},
            {"id": n[4], "type": "message",       "data": {"type": "message",      "label": "Bill Info",   "message": "Your current bill for {{mobileNumber}} is ₹499. Due date: 15th March."}, "position": _pos(540)},
            {"id": n[5], "type": "confirmation",  "data": {"type": "confirmation", "label": "Pay?",        "question": "Would you like to pay ₹499 now?", "yesLabel": "Yes", "noLabel": "No"}, "position": _pos(680)},
            {"id": n[6], "type": "tool",          "data": {"type": "tool",         "label": "Pay Bill",    "toolName": "payBill", "description": "Process bill payment"}, "position": _pos(820, 100)},
            {"id": n[7], "type": "end",           "data": {"type": "end",          "label": "End"},                                                                    "position": _pos(960)},
        ],
        "edges": [
            {"id": f"e_{n[0]}_{n[1]}", "source": n[0], "target": n[1]},
            {"id": f"e_{n[1]}_{n[2]}", "source": n[1], "target": n[2]},
            {"id": f"e_{n[2]}_{n[3]}", "source": n[2], "target": n[3]},
            {"id": f"e_{n[3]}_{n[4]}", "source": n[3], "target": n[4]},
            {"id": f"e_{n[4]}_{n[5]}", "source": n[4], "target": n[5]},
            {"id": f"e_{n[5]}_{n[6]}", "source": n[5], "target": n[6], "sourceHandle": "yes"},
            {"id": f"e_{n[5]}_{n[7]}", "source": n[5], "target": n[7], "sourceHandle": "no"},
            {"id": f"e_{n[6]}_{n[7]}", "source": n[6], "target": n[7]},
        ],
    }


def _network_issue_flow():
    n = [_nid() for _ in range(9)]
    return {
        "name": "Network Issue Flow",
        "metadata": {"intent": "network_issue"},
        "nodes": [
            {"id": n[0], "type": "start",        "data": {"type": "start",        "label": "Start"},                                                                     "position": _pos(0)},
            {"id": n[1], "type": "message",       "data": {"type": "message",      "label": "Greet",       "message": "I'm sorry you're facing a network issue. Let me look into it."},  "position": _pos(120)},
            {"id": n[2], "type": "entity",        "data": {"type": "entity",       "label": "Mobile No",   "entityName": "mobileNumber", "entityType": "phone", "prompt": "What is your mobile number?"}, "position": _pos(260)},
            {"id": n[3], "type": "entity",        "data": {"type": "entity",       "label": "Issue Type",  "entityName": "issueType", "entityType": "string", "prompt": "What kind of issue are you facing? (no signal / slow internet / call drops)"}, "position": _pos(400)},
            {"id": n[4], "type": "tool",          "data": {"type": "tool",         "label": "Diagnostics", "toolName": "runDiagnostics", "description": "Run network diagnostics on user's line"}, "position": _pos(560)},
            {"id": n[5], "type": "message",       "data": {"type": "message",      "label": "Result",      "message": "Diagnostics complete for {{mobileNumber}}. We've refreshed your network connection."}, "position": _pos(700)},
            {"id": n[6], "type": "confirmation",  "data": {"type": "confirmation", "label": "Resolved?",   "question": "Is your {{issueType}} issue resolved now?", "yesLabel": "Yes", "noLabel": "No"}, "position": _pos(840)},
            {"id": n[7], "type": "tool",          "data": {"type": "tool",         "label": "Ticket",      "toolName": "createTicket", "description": "Create support ticket"}, "position": _pos(980, 400)},
            {"id": n[8], "type": "end",           "data": {"type": "end",          "label": "End"},                                                                        "position": _pos(1120)},
        ],
        "edges": [
            {"id": f"e_{n[0]}_{n[1]}", "source": n[0], "target": n[1]},
            {"id": f"e_{n[1]}_{n[2]}", "source": n[1], "target": n[2]},
            {"id": f"e_{n[2]}_{n[3]}", "source": n[2], "target": n[3]},
            {"id": f"e_{n[3]}_{n[4]}", "source": n[3], "target": n[4]},
            {"id": f"e_{n[4]}_{n[5]}", "source": n[4], "target": n[5]},
            {"id": f"e_{n[5]}_{n[6]}", "source": n[5], "target": n[6]},
            {"id": f"e_{n[6]}_{n[8]}", "source": n[6], "target": n[8], "sourceHandle": "yes"},
            {"id": f"e_{n[6]}_{n[7]}", "source": n[6], "target": n[7], "sourceHandle": "no"},
            {"id": f"e_{n[7]}_{n[8]}", "source": n[7], "target": n[8]},
        ],
    }


def _plan_change_flow():
    n = [_nid() for _ in range(9)]
    return {
        "name": "Plan Change Flow",
        "metadata": {"intent": "plan_change"},
        "nodes": [
            {"id": n[0], "type": "start",        "data": {"type": "start",        "label": "Start"},                                                                    "position": _pos(0)},
            {"id": n[1], "type": "message",       "data": {"type": "message",      "label": "Greet",       "message": "I'll help you explore and change your plan."},   "position": _pos(120)},
            {"id": n[2], "type": "entity",        "data": {"type": "entity",       "label": "Mobile No",   "entityName": "mobileNumber", "entityType": "phone", "prompt": "What is your mobile number?"}, "position": _pos(260)},
            {"id": n[3], "type": "tool",          "data": {"type": "tool",         "label": "Fetch Plans", "toolName": "fetchPlans", "description": "Fetch available plans for user"}, "position": _pos(400)},
            {"id": n[4], "type": "message",       "data": {"type": "message",      "label": "Plans",       "message": "Here are the available plans:\n• ₹199 — 1.5 GB/day, 28 days\n• ₹399 — 2 GB/day, 56 days\n• ₹599 — 2.5 GB/day, 84 days"}, "position": _pos(540)},
            {"id": n[5], "type": "entity",        "data": {"type": "entity",       "label": "Choice",      "entityName": "selectedPlan", "entityType": "string", "prompt": "Which plan would you like to switch to?"}, "position": _pos(680)},
            {"id": n[6], "type": "confirmation",  "data": {"type": "confirmation", "label": "Confirm",     "question": "Switch {{mobileNumber}} to the {{selectedPlan}} plan?", "yesLabel": "Yes", "noLabel": "No"}, "position": _pos(820)},
            {"id": n[7], "type": "tool",          "data": {"type": "tool",         "label": "Change",      "toolName": "changePlan", "description": "Apply the new plan"}, "position": _pos(960, 100)},
            {"id": n[8], "type": "end",           "data": {"type": "end",          "label": "End"},                                                                       "position": _pos(1100)},
        ],
        "edges": [
            {"id": f"e_{n[0]}_{n[1]}", "source": n[0], "target": n[1]},
            {"id": f"e_{n[1]}_{n[2]}", "source": n[1], "target": n[2]},
            {"id": f"e_{n[2]}_{n[3]}", "source": n[2], "target": n[3]},
            {"id": f"e_{n[3]}_{n[4]}", "source": n[3], "target": n[4]},
            {"id": f"e_{n[4]}_{n[5]}", "source": n[4], "target": n[5]},
            {"id": f"e_{n[5]}_{n[6]}", "source": n[5], "target": n[6]},
            {"id": f"e_{n[6]}_{n[7]}", "source": n[6], "target": n[7], "sourceHandle": "yes"},
            {"id": f"e_{n[6]}_{n[8]}", "source": n[6], "target": n[8], "sourceHandle": "no"},
            {"id": f"e_{n[7]}_{n[8]}", "source": n[7], "target": n[8]},
        ],
    }


def _account_flow():
    n = [_nid() for _ in range(7)]
    return {
        "name": "Account Management Flow",
        "metadata": {"intent": "account"},
        "nodes": [
            {"id": n[0], "type": "start",   "data": {"type": "start",   "label": "Start"},                                                                              "position": _pos(0)},
            {"id": n[1], "type": "message",  "data": {"type": "message", "label": "Greet",    "message": "I'll help you with your account."},                            "position": _pos(120)},
            {"id": n[2], "type": "entity",   "data": {"type": "entity",  "label": "Mobile No","entityName": "mobileNumber", "entityType": "phone", "prompt": "Please share your registered mobile number."}, "position": _pos(260)},
            {"id": n[3], "type": "entity",   "data": {"type": "entity",  "label": "Request",  "entityName": "requestType", "entityType": "string", "prompt": "What would you like to do? (update address / SIM replacement / port number)"}, "position": _pos(400)},
            {"id": n[4], "type": "tool",     "data": {"type": "tool",    "label": "Process",  "toolName": "processAccountRequest", "description": "Submit account request"}, "position": _pos(560)},
            {"id": n[5], "type": "message",  "data": {"type": "message", "label": "Confirm",  "message": "Your {{requestType}} request for {{mobileNumber}} has been submitted. Reference: #REF-{{mobileNumber}}. You'll receive an SMS shortly."}, "position": _pos(700)},
            {"id": n[6], "type": "end",      "data": {"type": "end",     "label": "End"},                                                                                 "position": _pos(840)},
        ],
        "edges": [
            {"id": f"e_{n[0]}_{n[1]}", "source": n[0], "target": n[1]},
            {"id": f"e_{n[1]}_{n[2]}", "source": n[1], "target": n[2]},
            {"id": f"e_{n[2]}_{n[3]}", "source": n[2], "target": n[3]},
            {"id": f"e_{n[3]}_{n[4]}", "source": n[3], "target": n[4]},
            {"id": f"e_{n[4]}_{n[5]}", "source": n[4], "target": n[5]},
            {"id": f"e_{n[5]}_{n[6]}", "source": n[5], "target": n[6]},
        ],
    }


ALL_FLOWS = [
    _recharge_flow,
    _billing_flow,
    _network_issue_flow,
    _plan_change_flow,
    _account_flow,
]


# ---------------------------------------------------------------------------
# Public seeder
# ---------------------------------------------------------------------------

async def seed_mock_flows(db) -> int:
    """Insert mock intent flows if they don't already exist. Returns count inserted."""
    global _counter
    _counter = 0  # reset node id counter each seed run

    existing = await db.flows.count_documents({"orgId": ORG_ID, "projectId": PROJECT_ID})
    if existing >= len(ALL_FLOWS):
        log.info("Mock flows already seeded (%d found). Skipping.", existing)
        return 0

    now = datetime.utcnow()
    inserted = 0
    for builder in ALL_FLOWS:
        flow = builder()
        # Skip if this specific flow already exists
        if await db.flows.find_one({"orgId": ORG_ID, "projectId": PROJECT_ID, "name": flow["name"]}):
            continue

        doc = {
            "orgId": ORG_ID,
            "projectId": PROJECT_ID,
            "version": 1,
            "isDraft": False,
            **flow,
            "createdAt": now,
            "updatedAt": now,
        }
        await db.flows.insert_one(doc)
        inserted += 1
        log.info("Seeded flow: %s", flow["name"])

    log.info("Seeding complete. Inserted %d new flow(s).", inserted)
    return inserted
