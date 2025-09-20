# validator.py
import textwrap, re, json
from typing import List, Dict, Any, Optional
from settings import LLM
from tools import e2b_sandbox_tool

class Validator:
    """
    Generic validator: for each candidate method, ask LLM to produce self-contained Python script,
    run in sandbox (e2b_sandbox_tool), parse first JSON line as metrics.
    Fallback: small templates for common root-finding methods when possible.
    """
    def __init__(self, task_text: str, short_form: Optional[str]=None, domain_hint: Optional[str]=None,
                 candidate_methods: Optional[List[str]]=None, tol: float=1e-6, maxiter: int=200):
        self.task_text = task_text
        self.short_form = short_form
        self.domain_hint = domain_hint
        self.candidate_methods = candidate_methods
        self.tol = tol
        self.maxiter = maxiter

    def _clean(self, s: str) -> str:
        if not s: return s
        s = re.sub(r"^```(?:python)?\n", "", s, flags=re.I)
        s = re.sub(r"\n```$", "", s, flags=re.I)
        return s.strip()

    def _ask_methods(self) -> List[str]:
        prompt = f"Đề xuất 2-3 thuật toán phù hợp cho bài toán: {self.task_text}"
        r = LLM.invoke(prompt)
        txt = getattr(r, "content", str(r))
        parts = re.split(r"[\n,;]+", txt)
        methods = []
        for p in parts:
            t = p.strip()
            if t:
                methods.append(re.sub(r"^\d+\.\s*","",t))
        return methods[:6]

    def _ask_code(self, method: str) -> str:
        hint_f = f"Short form: {self.short_form}" if self.short_form else ""
        hint_dom = f"Domain: {self.domain_hint}" if self.domain_hint else ""
        prompt = textwrap.dedent(f"""
        Viết script Python để áp dụng phương pháp '{method}' cho bài toán:
        {self.task_text}
        {hint_f}
        {hint_dom}
        Yêu cầu: script in 1 dòng JSON duy nhất cuối cùng: {{ "method":..., "success": true/false, "iterations": int|null, "result": ..., "residual": float|null, "error": optional }}
        Tol={self.tol}, maxiter={self.maxiter}.
        """)
        r = LLM.invoke(prompt)
        return self._clean(getattr(r, "content", str(r)))

    def _fallback(self, method: str) -> str:
        # minimal fallback for root-finding when short_form exists
        f = self.short_form or "None"
        bracket = ""
        if self.domain_hint:
            try:
                s=self.domain_hint.strip(); a,b = s[1:-1].split(","); bracket=f"a={a}\nb={b}\n"
            except Exception:
                bracket=""
        templates = {
            "Bisection": f"""import json\n{bracket}def f(x): return {f}\ntry:\n a=locals().get('a',-10.0); b=locals().get('b',10.0)\n fa,fb=f(a),f(b)\n if fa*fb>0: raise ValueError('No bracket')\n it=0\n while it < {self.maxiter}:\n  c=(a+b)/2; fc=f(c)\n  if abs(fc)<{self.tol} or abs(b-a)/2<{self.tol}: break\n  it+=1\n  if fa*fc<=0: b=c; fb=fc\n  else: a=c; fa=fc\n print(json.dumps({{\"method\":\"Bisection\",\"success\":True,\"iterations\":it,\"result\":c,\"residual\":abs(fc)}}))\nexcept Exception as e:\n print(json.dumps({{\"method\":\"Bisection\",\"success\":False,\"error\":str(e)}}))""",
            "Secant": f"""import json\ndef f(x): return {f}\ntry:\n x0=1.0; x1=2.0\n for it in range({self.maxiter}):\n  fx0=f(x0); fx1=f(x1)\n  if abs(fx1-fx0)<1e-16: raise ZeroDivisionError('Denom')\n  x2 = x1 - fx1*(x1-x0)/(fx1-fx0)\n  if abs(x2-x1) < {self.tol} and abs(f(x2))<{self.tol}: x1=x2; break\n  x0,x1 = x1,x2\n print(json.dumps({{\"method\":\"Secant\",\"success\":True,\"iterations\":it,\"result\":x1,\"residual\":abs(f(x1))}}))\nexcept Exception as e:\n print(json.dumps({{\"method\":\"Secant\",\"success\":False,\"error\":str(e)}}))"""
        }
        return templates.get(method, templates.get("Secant"))

    def validate_methods(self, candidate_methods: Optional[List[str]] = None) -> List[Dict[str,Any]]:
        methods = candidate_methods or self.candidate_methods or self._ask_methods()
        methods = methods[:6]
        results = []
        for m in methods:
            code = ""
            try:
                code = self._ask_code(m)
                if not code or "print" not in code or "json" not in code:
                    code = self._fallback(m)
            except Exception:
                code = self._fallback(m)
            out = e2b_sandbox_tool.invoke(code)
            parsed = {"method": m, "raw_output": out}
            first_json = None
            for line in (out or "").splitlines():
                line=line.strip()
                if line.startswith("{") and line.endswith("}"):
                    first_json=line; break
            if first_json:
                try:
                    parsed_json = json.loads(first_json)
                    parsed.update(parsed_json)
                except Exception as e:
                    parsed["parse_error"] = str(e)
            else:
                parsed["parse_error"] = "no json line"
            results.append(parsed)
        return results

    def pick_best(self, results: List[Dict[str,Any]]) -> Dict[str,Any]:
        def score(r):
            if not r.get("success"): return float("inf")
            it = r.get("iterations") if isinstance(r.get("iterations"), (int,float)) else 1000
            res = r.get("residual") or 0.0
            return it + abs(res)
        succ = [r for r in results if r.get("success")]
        if succ:
            return min(succ, key=score)
        # fallback choose smallest residual
        def resid_key(r):
            v = r.get("residual") or r.get("result") or 1e9
            try: return abs(float(v))
            except: return float("inf")
        return min(results, key=resid_key)