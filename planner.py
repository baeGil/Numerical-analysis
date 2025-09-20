# planner.py
import textwrap, re, json
from settings import LLM
from pydantic import BaseModel, Field

class Plan(BaseModel):
    steps: list[str] = Field(...)

def make_plan(task_summary: str, method_name: str) -> Plan:
    prompt = textwrap.dedent(f"""
    Bạn là một nhà nghiên cứu toán học có khả năng giải quyết các bài toán phức tạp theo từng bước. Dựa trên:
    {task_summary}
    Thuật toán: {method_name}
    Hãy trả về JSON: {{ "steps": [ "step1", "step2", ... ] }}
    Mỗi step phải đủ để thực thi (input/output và nếu cần RUN_CODE).
    """)
    r = LLM.invoke(prompt)
    content = getattr(r, "content", str(r)).strip()
    m = re.search(r"\{.*\}", content, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            return Plan(steps=obj.get("steps",[]))
        except Exception:
            pass
    # fallback: split by lines
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    return Plan(steps=lines[:10])
