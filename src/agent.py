"""
Agent module for generating Python docstrings using Google's Gemini models.
Compatible with Python 3.12+.
"""

import os
import re
import ast
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# ----------------------------------------------------------------------
# 1. ENVIRONMENT – Find .env robustly
# ----------------------------------------------------------------------
possible_dotenv_paths = [
    Path.cwd() / ".env",
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent / ".env",
]

dotenv_path = None
for path in possible_dotenv_paths:
    if path.exists():
        dotenv_path = path
        break

if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(f"✅ Loaded .env from: {dotenv_path}")
else:
    print("⚠️  No .env file found. Relying on system environment variables.")

# ----------------------------------------------------------------------
# 2. API KEY – Try GOOGLE_API_KEY first, then GEMINI_API_KEY
# ----------------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GOOGLE_API_KEY:
    API_KEY = GOOGLE_API_KEY
    KEY_SOURCE = "GOOGLE_API_KEY"
elif GEMINI_API_KEY:
    API_KEY = GEMINI_API_KEY
    KEY_SOURCE = "GEMINI_API_KEY"
else:
    raise ValueError(
        "❌ No Gemini API key found. "
        "Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file."
    )

print(f"🔑 Using API key from: {KEY_SOURCE}")

# ----------------------------------------------------------------------
# 3. MODEL – gemini-flash-latest (available for all new keys)
# ----------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=API_KEY,
    temperature=0.1,
)

# ----------------------------------------------------------------------
# 4. PROMPT – One‑shot example with conditional syntax-error rule
# ----------------------------------------------------------------------
docstring_prompt = PromptTemplate(
    input_variables=["code"],
    template='''
You are an expert Python documentation agent. Your task is to add Google-style docstrings to the provided Python code.

**Rules:**
1. ONLY return the updated Python code. No explanations, no markdown fences.
2. Use **Google-style docstrings** (PEP 257) – triple quotes, Args/Returns sections indented **4 spaces inside** the docstring.
3. **DO NOT modify the logic or the structure of the code.** Keep the original function/class body exactly as is.
4. If the code **contains syntax errors**, still add docstrings wherever possible **and** add an inline comment `# TODO: Fix syntax error` **on the line after the function/class definition**.  
   If the code is **valid**, do NOT add any TODO comments.

**Example of correct output (valid code):**
def multiply(x, y):
    """Multiply two numbers.

    Args:
        x (int): First number.
        y (int): Second number.

    Returns:
        int: The product of x and y.
    """
    return x * y

**Now process this code:**
{code}
'''
)

# ----------------------------------------------------------------------
# 5. CHAIN
# ----------------------------------------------------------------------
chain = docstring_prompt | llm

# ----------------------------------------------------------------------
# 6. RESPONSE EXTRACTOR – Handles any format (string, list, dict)
# ----------------------------------------------------------------------
def extract_text_from_response(response) -> str:
    """Extract plain text from any response format."""
    if hasattr(response, 'content'):
        content = response.content
    else:
        content = response

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                texts.append(item.get('text', item.get('content', str(item))))
            elif isinstance(item, str):
                texts.append(item)
            else:
                texts.append(str(item))
        return ''.join(texts)
    if isinstance(content, dict):
        if 'text' in content:
            return content['text']
        if 'content' in content:
            return extract_text_from_response(content['content'])
        return str(content)
    return str(content)

# ----------------------------------------------------------------------
# 7. SYNTAX CHECKER
# ----------------------------------------------------------------------
def is_valid_python(code: str) -> bool:
    """Check if the code is syntactically valid Python."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

# ----------------------------------------------------------------------
# 8. DOCSTRING INDENTATION FIXER – Perfect Google style
# ----------------------------------------------------------------------
def fix_docstring_indentation(code: str) -> str:
    """Ensures Args/Returns are indented 4 spaces, descriptions 8 spaces."""
    lines = code.split('\n')
    fixed_lines = []
    i = 0
    in_docstring = False
    docstring_indent = 0

    while i < len(lines):
        line = lines[i]

        if '"""' in line and not in_docstring:
            in_docstring = True
            docstring_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            continue

        if in_docstring:
            stripped = line.lstrip()
            if stripped.startswith(('Args:', 'Returns:', 'Yields:', 'Raises:')):
                proper_indent = ' ' * (docstring_indent + 4)
                fixed_lines.append(proper_indent + stripped)
            elif stripped and not stripped.startswith('"""'):
                current_indent = len(line) - len(stripped)
                if current_indent <= docstring_indent + 4:
                    proper_indent = ' ' * (docstring_indent + 8)
                    fixed_lines.append(proper_indent + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

            if '"""' in line and line.strip().endswith('"""') and not line.strip().startswith('"""'):
                in_docstring = False
                docstring_indent = 0
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)

# ----------------------------------------------------------------------
# 9. POST-PROCESSOR – Only remove TODO comments if code was valid
# ----------------------------------------------------------------------
def clean_output(output: str, original_code: str) -> str:
    """
    - If original code is valid: remove any hallucinated '# TODO: Fix syntax error'.
    - If original code is invalid: keep (or add) the TODO comment.
    - Restore missing function body if the model stripped it.
    """
    lines = output.splitlines()

    # Only remove TODO comments if the original code is valid
    if is_valid_python(original_code):
        lines = [line for line in lines if "# TODO: Fix syntax error" not in line]

    cleaned = '\n'.join(lines).strip()

    # Restore missing body (rare, but safeguard)
    if cleaned.count('def ') == 1 and 'return' not in cleaned:
        match = re.search(r'"""(.*?)"""', cleaned, re.DOTALL)
        if match:
            docstring = match.group(0)
            sig_match = re.search(r'def \w+\([^)]*\):', cleaned)
            if sig_match:
                sig = sig_match.group(0)
                body_match = re.search(r':\s*(.*)', original_code, re.DOTALL)
                if body_match:
                    body = body_match.group(1).strip()
                    return f"{sig}\n    {docstring}\n    {body}"
                else:
                    return f"{sig}\n    {docstring}\n{original_code}"
    return cleaned

# ----------------------------------------------------------------------
# 10. MAIN FUNCTION
# ----------------------------------------------------------------------
def generate_docstrings(source_code: str) -> str:
    """
    Add Google-style docstrings to Python source code using Gemini.

    Args:
        source_code: Raw Python source code as a string.

    Returns:
        The same source code with docstrings inserted, or an error message.
    """
    if not source_code or not source_code.strip():
        return "# Error: The provided source code is empty."

    try:
        response = chain.invoke({"code": source_code})
        raw_output = extract_text_from_response(response).strip()

        # Remove accidental markdown fences
        if raw_output.startswith("```python"):
            raw_output = raw_output[9:]
        if raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]

        # Post-process: clean hallucinated TODOs and restore body
        raw_output = clean_output(raw_output, source_code)

        # Fix indentation inside docstrings
        raw_output = fix_docstring_indentation(raw_output)

        return raw_output.strip()

    except Exception as e:
        return f"# Error generating docstrings: {str(e)}"