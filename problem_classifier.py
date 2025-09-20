# problem_classifier.py
import textwrap, re, json
from settings import LLM

def classify_task(task_text: str) -> dict:
    """
    Return minimal classification but ALWAYS preserve original_task.
    Keys: category, short_form, domain_hint, notes, original_task
    """
    prompt = textwrap.dedent(f"""
    Bạn là chuyên gia toán và lập trình. Đọc đề bài sau (nguyên văn).
    Trả về MỘT KHỐI JSON gồm:
      - category: 'root_finding'|'linear_system'|'integration'|'ode_ivp'|'pde'|'optimization_unconstrained'|'other'
      - short_form: biểu thức Python tóm tắt nếu có (vd 'x**3 - x - 1') hoặc null
      - domain_hint: ví dụ '(1,2)' hoặc null
      - notes: ghi chú ngắn (tiếng Việt)
      - original_task: bản nguyên văn đề bài (PHẢI có)
    Đề bài:
    {task_text}
    """)
    resp = LLM.invoke(prompt)
    content = getattr(resp, "content", str(resp)).strip()
    # try parse JSON block
    m = re.search(r"\{.*\}", content, re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            data.setdefault("category", None)
            data.setdefault("short_form", None)
            data.setdefault("domain_hint", None)
            data.setdefault("notes", "")
            data["original_task"] = data.get("original_task") or task_text
            return data
        except Exception:
            pass
    # fallback heuristics but keep original_task
    lower = task_text.lower()
    if "tích phân" in lower or "integral" in lower:
        cat = "integration"
    elif "hệ phương trình" in lower or "ma trận" in lower:
        cat = "linear_system"
    elif "phương trình vi phân" in lower or "ode" in lower:
        cat = "ode_ivp"
    elif "pde" in lower:
        cat = "pde"
    elif "tìm nghiệm" in lower or "= 0" in lower or "giải phương trình" in lower:
        cat = "root_finding"
    elif "tối ưu" in lower or "cực trị" in lower:
        cat = "optimization_unconstrained"
    else:
        cat = "other"
    # simple short_form/domain extraction
    short = None
    dm = re.search(r"\(([0-9\.\-]+)\s*,\s*([0-9\.\-]+)\)", task_text)
    dom = f"({dm.group(1)},{dm.group(2)})" if dm else None
    m2 = re.search(r"(.+?)=\s*0", task_text)
    if m2:
        short = m2.group(1).strip().replace("^","**")
    return {"category":cat,"short_form":short,"domain_hint":dom,"notes":"fallback","original_task":task_text}