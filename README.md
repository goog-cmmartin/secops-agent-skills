# Google SecOps Agent Skills

A modular, version-controlled CLI tool designed to act as a "Skill Pack" for AI Agents interacting with Google SecOps (Chronicle) via the MCP API.

## Setup
1. Create a virtual environment: `python3 -m venv venv`
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure you have active Google Application Default Credentials: `gcloud auth application-default login`
4. Set up your environment variables by copying `.env.example` to `.env` and filling in your details:
   ```bash
   cp .env.example .env
   ```
   *(This allows you to omit `--project-id`, `--customer-id`, and `--region` from all commands!)*

## Agent Usage
If you are an AI Agent, read `skills/SECOPS_INDEX.md` to discover how to route user requests to the correct persona and tools.