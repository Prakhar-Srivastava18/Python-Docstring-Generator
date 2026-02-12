from pydantic import BaseModel

class CodeRequest(BaseModel):
    source_code: str
    filename: str = "snippet.py"

class CodeResponse(BaseModel):
    documented_code: str
    message: str