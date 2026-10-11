<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-0.1-0066CC?logo=graph&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-0.0.35-FF6B6B?logo=chain&logoColor=white"/>
  <img src="https://img.shields.io/badge/Postgres-Neon-336791?logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT4-7450C8?logo=openai&logoColor=white"/>
</p>

<h1 align="center">DataAgent: Autonomous Data Analytics Platform</h1>

<h3 align="center">Natural-language data analytics with LangGraph + LangChain + Python + Postgres (Neon)</h3>

<div align="center">
  <img src="https://img.shields.io/badge/status-Active-brightgreen"/>
  <img src="https://img.shields.io/badge/license-MIT-blue"/>
  <img src="https://img.shields.io/badge/PRs-welcome-orange"/>
</div>

---

## 🎯 Overview

An autonomous data analytics engine that bridges non-technical stakeholders and complex relational databases through **natural language interfaces**. Built on **LangGraph** with **LangChain-OpenAI** orchestration, it solves two core problems: accurate SQL generation from ambiguous intent and safe execution with validation gates.

## ⚡ Quick Stats

| Layer | Technology |
|-------|-----------|
| **Core** | LangGraph + LangChain + Python 3.14+ |
| **Database** | Postgres (Neon) serverless |
| **LLM** | Custom/Omniroute (Openai style) |
| **Validation** | Pydantic for data modeling |
| **Package Manager** | uv for dependency management |

## 🏗️ Architecture

```mermaid
graph TD
    Input([👤 User Input]) -->|Natural language query| Supervisor

    Supervisor[🧠 Router / Supervisor<br/>Classify intent]
    Supervisor -->|SQL intent| SQL[📊 SQL Analyst<br/>Generate query + context]
    Supervisor -->|ETL intent| ETL[🔄 ETL Analyst<br/>ReAct tool loop]

    SQL --> Judge
    ETL --> Execute

    subgraph Judge["🔒 Judge Gate"]
        J1["is_safe_sql validation"]
        J2["Schema validation"]
        J3["Read-only enforcement"]
    end

    Judge -->|safe| Execute[⚡ Execute / run tool]
    Judge -->|cancel| Reject[🚫 Cancel → explain & alternative]

    Execute --> Answer([💬 Render answer])
    Reject --> Answer
```

> **Key point:** every action a specialist proposes is checked by the judge gate (`is_safe_sql` → structured safe/cancel verdict) **before** execution — cancel branches into a safe explanation instead of a blind retry.

### SQL Analyst Workflow
1. **curate_question**: Understand user intent
2. **prompt_query_content**: Inject dynamic schema + 5 sample rows per table
3. **generate_sql_query**: Create SQL from natural language
4. **is_safe_sql**: Judge gate validation (returns structured safe/cancel verdict)
5. **(execute_sql | cancelled_sql)**: Branch based on safety validation
6. **represent_final_answer**: Format results for user presentation

### ETL Analyst Workflow (ReAct Loop)
- **Think**: Determine what action to take next
- **Act**: Execute selected tool (API fetch, data transformation, etc.)
- **Observe**: Analyze results and decide next step
- Loop continues until task completion

## 🗺️ Project Structure

```text
DataAgent/
├── Models/
│   └── schema.py          # Pydantic state definitions
├── agents/
│   ├── sql_analyst.py     # SQL analysis with safety validation
│   ├── etl_analyst.py     # ETL automation with ReAct loop
│   └── data_agent.py      # Main orchestrator and entry point
├── utils/
│   ├── llm_pick.py        # Intelligent LLM selection
│   ├── database.py        # Schema introspection + SQL execution
│   └── etl_tools.py       # API fetching + Pandas transformations
├── data/
│   └── extract/           # Source data files
├── .env                   # Environment variables (DATABASE_URL, LLM keys)
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules
├── .python-version        # Python version requirement
├── INTERVIEW_GUIDE.md     # Interview preparation guide
├── README.md              # This file
├── main.py                # Application entry point
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies (backup)
└── uv.lock                # uv lockfile (reproducible builds)
```

## ✨ Features

### Completed
| Feature | Details |
|---------|---------|
| **Multi-Agent Architecture** | Router + SQL/ETL specialists pattern |
| **Judge Gate Validation** | LLM validation before execution (structured output) |
| **Dynamic Schema Injection** | Real-time table introspection from `information_schema` |
| **ReAct Loop** | ETL agent with custom Python tools for API/data processing |
| **Natural Language Interface** | Query databases without SQL knowledge |
| **Audit Trails** | Complete logging of all operations |
| **Custom Tools** | API fetching, Pandas transformations, file exports |
| **Production Deployment** | Running with active usage |

### Technical Implementation
- **LangGraph**: Stateful workflow orchestration with conditional branching
- **LangChain-OpenAI**: LLM integration for natural language processing
- **Python 3.14+**: Core business logic with Pydantic data validation
- **Neon Postgres**: Serverless database with pay-per-query pricing
- **Pydantic Models**: `AgentSchema`, `JudgeSchema`, `ETLAgentSchema`

## 🚀 Getting Started

### Prerequisites
- Python >= 3.14
- uv package manager
- Postgres (Neon) database
- LLM provider API key (OpenAI, etc.)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd DataAgent

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Set DATABASE_URL and LLM API keys in .env
# Example: DATABASE_URL="postgresql://user:pass@neon.aws.com:5432/dbname"
# Example: OPENAI_API_KEY="sk-..."

# Initialize database with sample data
uv run feed_db.py

# Start the SQL analyst agent (default)
uv run agents/sql_analyst.py

# To start ETL analyst instead:
uv run agents/etl_analyst.py
```

## 📝 Usage Examples

### SQL Query Example
**User Input:** "Show me the total number of students present today"
**Process:**
1. Router classifies as SQL intent
2. SQL Analyst injects current schema + 5 sample rows per table
3. Generates SQL: SELECT COUNT(*) FROM attendance WHERE status = 'present' AND date = CURDATE()
4. Judge Gate validates: SELECT only, read-only operation
5. Executes against Postgres database
6. Returns natural language response with count

### ETL Task Example
**User Input:** "Fetch latest weather data and save as CSV"
**Process:**
1. Router classifies as ETL intent
2. ETL Analyst enters ReAct loop:
   - Think: Need to call weather API
   - Act: Fetch data from OpenWeatherMap API
   - Observe: Received JSON payload
   - Think: Need to normalize and save as CSV
   - Act: Transform data with Pandas, export to CSV file
   - Observe: File created successfully
3. Returns confirmation with file location



## 📄 License

MIT License — see [LICENSE](LICENSE) for details.