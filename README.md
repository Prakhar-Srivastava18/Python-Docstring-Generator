# Docstring Generator Agent

This project builds an AI agent that reads Python source code and automatically generates clear, meaningful docstrings for Functions, Classes, and Methods.

## Setup Instructions

1. Create a virtual environment:
   `python -m venv venv`
2. Activate the virtual environment:
   * Windows: `venv\Scripts\activate`
   * Mac/Linux: `source venv/bin/activate`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Add your Gemini API key to the `.env` file.
5. Run the server:
   `uvicorn src.__main__:app --reload`