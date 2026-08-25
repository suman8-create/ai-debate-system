from langgraph.graph import StateGraph, END
from graph.state import DebateState
from graph.nodes import (
    research_node,
    pro_generate_node,
    pro_audit_node,
    con_generate_node,
    con_audit_node,
    conflict_resolver_node,
    round_increment_node,
    judge_node
)
from graph.edges import (
    check_pro_audit_verdict,
    check_con_audit_verdict,
    check_round_limit
)

def build_debate_graph():
    workflow = StateGraph(DebateState)

    # 1. Register Nodes
    workflow.add_node("research", research_node)
    workflow.add_node("pro_generate", pro_generate_node)
    workflow.add_node("pro_audit", pro_audit_node)
    workflow.add_node("con_generate", con_generate_node)
    workflow.add_node("con_audit", con_audit_node)
    workflow.add_node("conflict_resolver", conflict_resolver_node)
    workflow.add_node("round_increment", round_increment_node)
    workflow.add_node("judge", judge_node)

    # 2. Build Pipeline Flow
    workflow.set_entry_point("research")
    workflow.add_edge("research", "pro_generate")
    workflow.add_edge("pro_generate", "pro_audit")

    # PRO Audit Conditional Edge
    workflow.add_conditional_edges(
        "pro_audit",
        check_pro_audit_verdict,
        {
            "proceed_to_con": "con_generate",
            "retry_pro": "pro_generate"
        }
    )

    workflow.add_edge("con_generate", "con_audit")

    # CON Audit Conditional Edge
    workflow.add_conditional_edges(
        "con_audit",
        check_con_audit_verdict,
        {
            "proceed_to_conflict": "conflict_resolver",
            "retry_con": "con_generate"
        }
    )

    workflow.add_edge("conflict_resolver", "round_increment")

    # Round Limit Conditional Edge
    workflow.add_conditional_edges(
        "round_increment",
        check_round_limit,
        {
            "next_round": "pro_generate",
            "adjudicate": "judge"
        }
    )

    workflow.add_edge("judge", END)

    return workflow.compile()

# Singleton compiled graph instance
debate_graph = build_debate_graph()