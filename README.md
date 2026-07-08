# AI Cloud Cost Optimiser

A full-stack MVP that lets users upload cloud billing exports in CSV format and receive AI-generated cost-optimisation suggestions.

## Architecture

- Backend: Python + FastAPI
- Frontend: Streamlit
- LLM: Groq API via the model `llama-3.1-8b-instant`
- Parsing: Pandas

## Project structure

- backend/ - FastAPI app, CSV parsing, analysis logic, and LLM integration
- frontend/ - Streamlit UI for uploading bills and displaying results
- sample_data/ - Example CSV files for AWS, Azure, and GCP exports

## Prerequisites

- Python 3.10+
- A free Groq API key: https://console.groq.com/keys

## Setup

1. Create and activate a virtual environment
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.\.venv\Scripts\Activate.ps1`

2. Install dependencies
   - Backend:
     - `pip install -r backend/requirements.txt`
   - Frontend:
     - `pip install -r frontend/requirements.txt`

3. Configure environment variables
   - Copy `.env.example` to `.env`
   - Fill in your Groq API key

4. Run the backend
   - `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`

5. Run the frontend
   - `streamlit run frontend/app.py`

## Sample data

You can test the app with the sample CSV files in the sample_data folder.

## Notes

- The current scaffold includes boilerplate code and TODO-friendly structure.
- The LLM integration uses the Groq API when a valid key is present; otherwise it falls back to deterministic placeholder suggestions.
