import logging

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import analyze_node, decision_node, planner_node, question_node, report_node
from app.agents.state import InterviewState

logger = logging.getLogger("career_agent.interview_agent")


def _entry_route(state: InterviewState) -> str:
    return "planner" if state.get("mode") == "start" else "analyze"


def _decision_route(state: InterviewState) -> str:
    return "report" if state.get("next_action") == "finish" else "question"


def build_interview_graph():
    builder = StateGraph(InterviewState)
    builder.add_node("planner", planner_node)
    builder.add_node("question", question_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("decision", decision_node)
    builder.add_node("report", report_node)
    builder.add_conditional_edges(START, _entry_route, {"planner": "planner", "analyze": "analyze"})
    builder.add_edge("planner", "question")
    builder.add_edge("question", END)
    builder.add_edge("analyze", "decision")
    builder.add_conditional_edges("decision", _decision_route, {"question": "question", "report": "report"})
    builder.add_edge("report", END)
    return builder.compile()


class InterviewAgent:
    def __init__(self) -> None:
        self.graph = build_interview_graph()

    async def start(self, state: InterviewState) -> InterviewState:
        logger.info("[%s] graph start job=%s", state["session_id"], state["job"])
        return await self.graph.ainvoke({**state, "mode": "start"})

    async def chat(self, state: InterviewState, answer: str) -> InterviewState:
        messages = [*state.get("messages", []), {"role": "user", "content": answer}]
        logger.info("[%s] graph resume answer_chars=%s", state["session_id"], len(answer))
        return await self.graph.ainvoke({**state, "mode": "chat", "messages": messages})


interview_agent = InterviewAgent()
