import re
from dotenv import load_dotenv
from langchain_core.tools import tool, StructuredTool
from e2b_code_interpreter import Sandbox
from settings import LLM

load_dotenv()
llm = LLM

def extract_missing_module(error_msg: str) -> str:
    """Trích xuất tên module bị thiếu từ error message"""
    pattern = r"No module named '([^']+)'"
    match = re.search(pattern, error_msg)
    return match.group(1) if match else None

def get_install_command(missing_module: str, llm) -> str:
    prompt = f"""
I got this error: "No module named '{missing_module}'"
Please provide ONLY the pip install command to fix this error.
Return only the command, no explanation, no code blocks.
Example: pip install torch
"""
    try:
        response = llm.invoke(prompt)
        command = getattr(response, "content", str(response)).strip()
        if not command.startswith("pip install"):
            command = f"pip install {missing_module}"
        return command
    except Exception:
        return f"pip install {missing_module}"

def execute_python_raw(code: str, max_install_attempts: int = 5) -> str:
    """
    Run code in E2B sandbox. Auto-install missing modules by asking LLM for pip command.
    Returns stdout/text or an error message.
    """
    attempt = 0
    try:
        with Sandbox.create() as sandbox:
            while attempt < max_install_attempts:
                execution = sandbox.run_code(code)
                # success
                if not execution.error:
                    output = getattr(execution.logs, "stdout", "")
                    if isinstance(output, list):
                        output = "".join(str(line) for line in output)
                    if output:
                        return output.strip()
                    if getattr(execution, "text", None):
                        return execution.text.strip()
                    return "No output"
                # error -> check missing module
                error_msg = execution.error.traceback
                missing_module = extract_missing_module(error_msg)
                if missing_module:
                    install_command = get_install_command(missing_module, llm)
                    try:
                        sandbox.commands.run(install_command)
                    except Exception as ie:
                        print("Install failed:", ie)
                    attempt += 1
                    continue
                # other error
                return f"Error: {error_msg}"
            return f"Error: Max install attempts ({max_install_attempts}) reached. Last error: {execution.error.traceback}"
    except Exception as e:
        return f"Error: {e}"

# Wrap as StructuredTool so create_react_agent can call it
e2b_sandbox_tool = StructuredTool.from_function(
    func=execute_python_raw,
    name="e2b_sandbox",
    description=(
        "Run vetted Python code in an isolated sandbox. "
        "Call only when you have a concrete code block to execute and expect stdout/text back."
    ),
    handle_tool_error=True
)