# algorithm_researcher.py
import textwrap, json, re
from settings import LLM
from algorithm_map import ALGORITHM_MAP

def research_and_propose(task_text: str, category_hint: str = None, short_form: str = None, domain_hint: str = None) -> dict:
    """
    Return: { candidate_methods: [...], reasoning: str, research_actions: str }
    Prefer JSON from LLM; fallback to ALGORITHM_MAP.
    """
    prompt = textwrap.dedent(f"""
    Bạn là nhà nghiên cứu thuật toán số. Dựa trên:
    - category_hint: {category_hint}
    - short_form: {short_form}
    - domain: {domain_hint}
    - task: {task_text}

    Đề xuất khoảng 2-3 phương pháp phù hợp (không liệt kê tất cả). Với mỗi phương pháp hãy nêu lí do lựa chọn.
    Trả về kết quả dưới dạng JSON: {{ "candidate_methods": [...], "reasoning":"...", "research_actions":"..." }}
    """)
    resp = LLM.invoke(prompt)
    content = getattr(resp, "content", str(resp)).strip()
    m = re.search(r"\{.*\}", content, re.S)
    if m:
        try:
            out = json.loads(m.group(0))
            if out.get("candidate_methods"):
                return out
        except Exception:
            pass
    # fallback: choose from map
    cat = category_hint or "root_finding"
    methods = ALGORITHM_MAP.get(cat, [])[:6]
    return {"candidate_methods": methods, "reasoning": "", "research_actions": ""}
