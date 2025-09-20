# main.py
import asyncio, operator
from typing import TypedDict, Annotated, Literal
from langchain.agents import load_tools
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from settings import LLM
from problem_classifier import classify_task
from algorithm_researcher import research_and_propose
from algorithm_map import ALGORITHM_MAP
from planner import make_plan, Plan
from validator import Validator
from tools import e2b_sandbox_tool

# web tools (search/arxiv/wiki)
search_tools = load_tools(["ddg-search","arxiv","wikipedia"], llm=LLM)
tools = search_tools + [e2b_sandbox_tool]

# execution agent: runs steps, can call tools
system_prompt = "Bạn là trợ lý thực thi các bước; ưu tiên ArXiv->Search->Wikipedia để research; chỉ gọi sandbox khi có code hoàn chỉnh."
step_template = "TASK:\n{task}\n\nPLAN:\n{plan}\n\nSTEP TO EXECUTE:\n{step}\n"
prompt_template = ChatPromptTemplate.from_messages([("system",system_prompt),("user",step_template)])
execution_agent = create_react_agent(
    model=LLM,
    tools=tools,
    state_schema=AgentState
)

# Graph state
class PlanState(TypedDict):
    task: str
    classification: dict
    research: dict
    validation_results: list
    best_algorithm: dict
    plan: Plan
    past_steps: Annotated[list[str], operator.add]
    final_response: str

def get_current_step(state: PlanState) -> int:
    return len(state.get("past_steps", []))

def get_full_plan(state: PlanState) -> str:
    out=[]
    for i, s in enumerate(state["plan"].steps):
        txt=f"# {i+1}. {s}\n"
        if i<get_current_step(state): txt+=f"Result: {state['past_steps'][i]}\n"
        out.append(txt)
    return "\n".join(out)

final_prompt = PromptTemplate.from_template("TASK:\n{task}\n\nPLAN+RESULTS:\n{plan}\n\nFINAL ANSWER:\n")

# nodes
async def _classify(state: PlanState) -> PlanState:
    cls = classify_task(state["task"])
    return {"classification": cls}

async def _research(state: PlanState) -> PlanState:
    cls = state["classification"]
    ar = research_and_propose(state["task"], category_hint=cls.get("category"), short_form=cls.get("short_form"), domain_hint=cls.get("domain_hint"))
    if not ar.get("candidate_methods"):
        ar["candidate_methods"] = ALGORITHM_MAP.get(cls.get("category"), list(ALGORITHM_MAP.values())[0])[:6]
    return {"research": ar}

async def _validate(state: PlanState) -> PlanState:
    ar = state["research"]
    cls = state["classification"]
    validator = Validator(task_text=state["task"], short_form=cls.get("short_form"), domain_hint=cls.get("domain_hint"), candidate_methods=ar.get("candidate_methods"))
    results = validator.validate_methods(ar.get("candidate_methods"))
    best = validator.pick_best(results)
    return {"validation_results": results, "best_algorithm": best}

async def _plan(state: PlanState) -> PlanState:
    best_name = state["best_algorithm"].get("method") or state["research"]["candidate_methods"][0]
    summary = f"Method: {best_name}\nShort: {state['classification'].get('short_form')}\nDomain: {state['classification'].get('domain_hint')}\nTask: {state['task']}"
    plan = make_plan(task_summary=summary, method_name=best_name)
    return {"plan": plan}

async def _run_step(state: PlanState) -> PlanState:
    plan = state["plan"]
    idx = get_current_step(state)
    step_text = plan.steps[idx]
    # Nội dung user từ template
    user_content = step_template.format(
        task=state["task"],
        plan=get_full_plan(state),
        step=step_text
    )
    # Truyền vào agent dạng messages
    res = await execution_agent.ainvoke({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    })
    # Lấy output cuối từ agent
    messages = res.get("messages", [])
    content = messages[-1].content if messages else str(res)
    return {"past_steps": [content]}

async def _final(state: PlanState) -> PlanState:
    final = await (final_prompt | LLM).ainvoke({"task": state["task"], "plan": get_full_plan(state)})
    return {"final_response": final}

def _should_continue(state: PlanState) -> Literal["run","final"]:
    return "run" if get_current_step(state) < len(state["plan"].steps) else "final"

# build graph
builder = StateGraph(PlanState)
builder.add_node("classify", _classify)
builder.add_node("research", _research)
builder.add_node("validate", _validate)
builder.add_node("plan", _plan)
builder.add_node("run", _run_step)
builder.add_node("final", _final)
builder.add_edge(START, "classify")
builder.add_edge("classify","research")
builder.add_edge("research","validate")
builder.add_edge("validate","plan")
builder.add_edge("plan","run")
builder.add_conditional_edges("run", _should_continue)
builder.add_edge("final", END)
graph = builder.compile()

# runner
async def run_task(task_text: str):
    print("\n=== RUNNING PIPELINE ===\n")
    final_res = None
    # stream theo event v1 thay vì raw updates
    async for event in graph.astream_events({"task": task_text}, version="v1"):
        etype = event["event"]
        name = event.get("name")
        # In khi node kết thúc
        if etype == "on_chain_end":
            if name == "classify":
                print("\n[CLASSIFY] ->", event["data"]["output"])
            elif name == "research":
                print("\n[RESEARCH] ->", event["data"]["output"])
            elif name == "validate":
                print("\n[VALIDATE] ->", event["data"]["output"]["best_algorithm"])
            elif name == "plan":
                plan = event["data"]["output"]["plan"]
                print("\n[PLAN] ->")
                for i, s in enumerate(plan.steps, 1):
                    print(f"  {i}. {s}")
            elif name == "run":
                step_out = event["data"]["output"]["past_steps"][-1]
                print("\n[RUN STEP] ->", step_out)
            elif name == "final":
                final_res = event["data"]["output"]["final_response"]
                print("\n[FINAL RESPONSE] ->", final_res)
    print("\n=== FINAL ===\n", final_res)
    return final_res

if __name__ == "__main__":
    sample = "Bằng phương pháp dây cung, tìm nghiệm gần đúng của phương trình sau: x**3 - x - 1 = 0 trong khoảng phân ly nghiệm (1, 2), với sai số epsilon = 10e-5."
    # sample = "Tính thể tích hình cầu với sáu chữ số đáng tin biết đường kính d là nghiệm dương lớn nhất của phương trình 3*sin(x) + x**3 - 8*x**2 + 8*x + 1 = 0; pi lấy đúng 7 chữ số sau dấu phẩy. Ghi bảng lặp."
    asyncio.run(run_task(sample))