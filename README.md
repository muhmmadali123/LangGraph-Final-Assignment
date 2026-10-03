# LangGraph Final Assignment

A multi-agent AI system built with **LangGraph**, **Groq**, **Pinecone**, **GitHub**, **Google Calendar**, and **Gmail**.

This project contains a RAG sub-agent and MCP-integrated agents for GitHub, Google Calendar, and Gmail.

## Assignment Requirements

This project implements:

1. A complete RAG sub-agent using a PDF stored in a hosted vector database.
2. A GitHub MCP sub-agent for GitHub-related questions.
3. A Google Calendar agent for reading and creating meetings.
4. A Gmail agent for writing, drafting, and sending emails.

---

## Project Architecture

```text
User
 │
 ▼
LangGraph Supervisor
 │
 ├── RAG Agent
 │     ├── PDF
 │     ├── Sentence Transformers
 │     ├── Pinecone
 │     └── Groq
 │
 ├── GitHub Agent
 │     └── GitHub MCP Server
 │
 ├── Calendar Agent
 │     └── Google Calendar MCP Server
 │
 └── Email Agent
       └── Gmail MCP Server

```

---

## Features

### 1. RAG Agent

The RAG agent answers questions from a PDF document.

The project uses:

- PDF document
- `pypdf` for PDF extraction
- `RecursiveCharacterTextSplitter` for chunking
- `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- Pinecone as the hosted vector database
- Groq for generating the final answer

The current PDF is:

```text
data/documents/Attendace register.pdf

```

Example question:

```text
What information is available in the attendance register?

```

The agent retrieves relevant information from Pinecone and generates an answer using the retrieved PDF context.

---

### 2. GitHub Agent

The GitHub agent provides GitHub-related information.

It can:

- Get GitHub user information
- Get repository information
- List repository issues
- Read repository README files

Example questions:

```text
Tell me about microsoft/vscode

```

```text
Show issues in microsoft/vscode

```

```text
Tell me about the GitHub account microsoft

```

The GitHub integration is implemented using an MCP server with GitHub API access.

---

### 3. Google Calendar Agent

The Calendar agent is integrated with Google Calendar.

It can:

- Read upcoming meetings
- Create calendar meetings
- Create meetings at specific start and end times
- Understand natural-language meeting requests

Example:

```text
Show my upcoming meetings

```

```text
Create a meeting called AI Class tomorrow at 4 PM for 1 hour

```

```text
Fix my meeting tomorrow from 5 to 6 PM

```

The calendar uses the Pakistan timezone:

```text
Asia/Karachi

```

Google OAuth credentials are stored locally and are not committed to GitHub.

---

### 4. Gmail Agent

The Gmail agent is integrated with Gmail.

It can:

- Write emails
- Create email drafts
- Send emails

Example:

```text
Draft an email to my teacher about my LangGraph assignment

```

```text
Send an email to example@gmail.com about my assignment

```

The Gmail integration uses the Gmail API and OAuth authentication.

---

## Technologies Used

- Python 3.14
- LangGraph
- LangChain
- Groq
- Pinecone
- Sentence Transformers
- PyGithub
- Model Context Protocol (MCP)
- Google Calendar API
- Gmail API
- FastAPI-compatible project structure
- OAuth 2.0

---

## Project Structure

```text
LangGraph-Final-Assignment/
│
├── app/
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── rag_agent.py
│   │   ├── github_agent.py
│   │   ├── calendar_agent.py
│   │   └── email_agent.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── graph/
│   │   └── workflow.py
│   │
│   ├── mcp/
│   │   ├── github_server.py
│   │   ├── calendar_server.py
│   │   └── email_server.py
│   │
│   └── rag/
│       ├── ingest.py
│       ├── retriever.py
│       └── vectorstore.py
│
├── data/
│   └── documents/
│       └── Attendace register.pdf
│
├── tests/
│
├── main.py
├── requirements.txt
├── .gitignore
├── .env
├── credentials.json
├── token.json
└── gmail_token.json

```

> Secret files such as `.env`, `credentials.json`, `token.json`, and `gmail_token.json` are excluded from Git using `.gitignore`.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/muhmmadali123/LangGraph-Final-Assignment.git

```

Go into the project:

```bash
cd LangGraph-Final-Assignment

```

---

### 2. Create a virtual environment

```bash
python -m venv .venv

```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1

```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt

```

---

## Environment Variables

Create a `.env` file in the project root.

Add:

```env
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=langgraph-final-assignment
GITHUB_TOKEN=your_github_token

```

Do not upload API keys or OAuth credentials to GitHub.

---

## Pinecone Setup

The project uses Pinecone as the hosted vector database.

The Pinecone index should use:

```text
Index name: langgraph-final-assignment
Dimension: 384
Metric: cosine

```

The embedding model is:

```text
sentence-transformers/all-MiniLM-L6-v2

```

To ingest a PDF:

```bash
python -m app.rag.ingest "data/documents/Attendace register.pdf"

```

Example output:

```text
Loading PDF: data/documents/Attendace register.pdf
Created 2 chunks.
Uploaded 2 vectors to Pinecone.

```

---

## Google Calendar Setup

Google Calendar requires OAuth authentication.

The Google Cloud project must have the Google Calendar API enabled.

Place the downloaded OAuth desktop credentials in:

```text
credentials.json

```

When the application authenticates for the first time, an OAuth token is created:

```text
token.json

```

These files must remain private.

---

## Gmail Setup

The Gmail API must be enabled in Google Cloud.

The Gmail agent uses OAuth authentication.

The authentication token is stored locally as:

```text
gmail_token.json

```

This file is excluded from Git.

---

## Running the Application

Start the application with:

```bash
python main.py

```

The application runs continuously and accepts multiple questions.

Example:

```text
============================================================
LangGraph Final Assignment
Multi-Agent AI System
============================================================
Type 'exit' or 'quit' to stop.
Press Ctrl+C anytime to stop.
============================================================

You:

```

You can enter multiple requests without restarting the application.

---

## Example Queries

### RAG

```text
What information is available in the attendance register?

```

### GitHub

```text
Tell me about microsoft/vscode

```

```text
Show issues in microsoft/vscode

```

### Google Calendar

```text
Show my upcoming meetings

```

```text
Create a meeting called AI Class tomorrow at 4 PM for 1 hour

```

### Gmail

```text
Draft an email to my teacher about my LangGraph assignment

```

```text
Send an email to example@gmail.com about my assignment

```

---

## Security

The following files contain private credentials and should never be committed:

```text
.env
credentials.json
token.json
gmail_token.json

```

The virtual environment is also excluded:

```text
.venv/

```

The `.gitignore` file protects these files from being uploaded accidentally.

---

## LangGraph Workflow

The application uses LangGraph to manage the main workflow.

The supervisor receives the user's request and routes it to the appropriate specialist agent.

```text
User Request
     │
     ▼
Supervisor
     │
     ├── RAG Agent
     │
     ├── GitHub Agent
     │
     ├── Calendar Agent
     │
     └── Email Agent

```

Each specialist agent performs its specific task and returns the result to the user.

---

## Assignment Requirement Mapping


| Requirement         | Implementation                          |
| ------------------- | --------------------------------------- |
| LangGraph Agent     | `app/graph/workflow.py`                 |
| RAG Sub-Agent       | `app/agents/rag_agent.py`               |
| Hosted Vector Store | Pinecone                                |
| PDF Document        | `data/documents/Attendace register.pdf` |
| GitHub MCP          | `app/mcp/github_server.py`              |
| GitHub Agent        | `app/agents/github_agent.py`            |
| Google Calendar     | `app/mcp/calendar_server.py`            |
| Calendar Agent      | `app/agents/calendar_agent.py`          |
| Gmail Integration   | `app/mcp/email_server.py`               |
| Email Agent         | `app/agents/email_agent.py`             |
| Main Application    |                                         |


