# AUTOTEST: Automated Test Case and Selenium/Playwright Script Generation using LLM

<img src="./autotest_image.jpg" alt="Project Logo" width="100" height="auto">

AUTOTEST is an open-source GenAI-powered web application for automated test case and Selenium/Playwright script generation. It leverages large language models (LLMs) to analyze web pages, discover site structure via BFS URL extraction, generate comprehensive test scenarios and test cases, and produce executable Python test scripts — all through a modern web-based interface.

## Table of Contents

- [Description](#description)
- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [LLM Configuration](#llm-configuration)
- [Contributing](#contributing)
- [Future Scope and Improvements](#future-scope-and-improvements)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Description

AUTOTEST is a GenAI-powered web application that automates the generation of test cases and Python Selenium/Playwright scripts for web applications. After a site URL is added, the system performs recursive unique internal URL extraction using Breadth-First Search (BFS), analyzes each discovered page to extract metadata, generates page-specific test scenarios and test cases, and produces executable test scripts.

The application supports valid and invalid test data sets for authentication and form testing, context-aware test case generation using full page HTML and metadata, and a visual drag-and-drop test suite builder. All major open-source and closed-source LLMs are supported through a configurable LLM abstraction layer.

---

## Architecture Overview

The application consists of three main components:

| Component | Technology |
|-----------|-----------|
| Frontend  | React, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Flow, React Query, WebSocket |
| Backend   | Python, FastAPI, SQLAlchemy ORM, Alembic, PostgreSQL, authentication middleware |
| Shared    | `shared_orm` package — SQLAlchemy model definitions shared across services |

---

## Features

### Site Management
Add sites by URL and track their analysis status (New / Processing / Done) from a centralized dashboard.

### Automatic Page Discovery
BFS-based URL extraction crawls the target site up to a configurable depth, building a complete list of unique internal pages per site.

### AI-Powered Test Scenario Generation
Each discovered page is analyzed using LLMs (default: OpenAI GPT-4o) to generate page-specific test scenarios. Both page HTML source and extracted metadata are provided to the model for context-aware generation.

### Test Case Management
Generated test scenarios contain individual test cases covering positive and negative flows. Test cases include structured steps, selectors, validation criteria, and valid/invalid test data sets. Full CRUD operations are supported.

### Test Suite Builder
A visual drag-and-drop flow editor built with React Flow allows users to construct test suites by:
- Adding test scenario nodes, branch nodes, and end nodes to the canvas
- Connecting nodes with directed edges and setting conditions on those edges
- Assigning site attribute values to individual nodes
- Referencing other saved test suites as reusable sub-nodes

### Site Attributes
Define reusable key-value attribute pairs per site (for example, credentials or environment-specific variables) that can be assigned to nodes within the test suite builder.

### Test Script Generation
Automatically generate executable Python Selenium or Playwright scripts for any test scenario directly from the UI.

### Schedule and Configuration
Configure per-site test scheduling and LLM settings through the application settings interface.

### Real-Time Updates
WebSocket connections provide live status updates for page analysis and test generation tasks without requiring page refreshes.

### Dual Model Support
The system uses separate configurable LLM models for page analysis/test generation and for script generation, allowing independent optimization of each task.

### Broad LLM Provider Support
All major open-source and closed-source LLM providers are supported via LangChain's abstraction layer and the `llm_config.yaml` configuration file.

---

## Project Structure

```
AUTOTEST/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── routers/          # API endpoint definitions
│   │   ├── services/         # Business logic and LLM integrations
│   │   ├── schemas/          # Pydantic request/response models
│   │   └── app.py            # FastAPI application entry point
│   ├── alembic/              # Database migration scripts
│   ├── llm_config.yaml       # LLM provider and model configuration
│   └── requirements.txt
├── frontend/                 # React + TypeScript application
│   └── src/
│       ├── components/       # UI components (shadcn/ui, React Flow nodes, etc.)
│       ├── utils/            # Utility functions and API client helpers
│       └── types/            # TypeScript type definitions
├── shared/                   # Shared SQLAlchemy ORM package
│   └── shared_orm/
│       └── models/           # Database model definitions
└── README.md
```

---

## Getting Started

### Backend Setup

**Prerequisites:** Python 3.10 or later, PostgreSQL

1. Clone the repository and navigate to the backend directory:
   ```bash
   git clone <repository-url>
   cd AUTOTEST/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the shared ORM package (from the repo root):
   ```bash
   pip install -e ../shared
   ```

5. Configure environment variables (see [Environment Variables](#environment-variables)).

6. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the development server:
   ```bash
   uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
   ```

---

### Frontend Setup

**Prerequisites:** Node.js 18 or later, npm

1. Navigate to the frontend directory:
   ```bash
   cd AUTOTEST/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables (see [Environment Variables](#environment-variables)).

4. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` by default.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/autotest` |
| `SECRET_KEY` | Secret key used for authentication token signing |
| `OPENAI_API_KEY` | API key for OpenAI (or replace with the appropriate key for your chosen LLM provider) |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Base URL of the backend API, e.g. `http://localhost:8000` |

---

## LLM Configuration

LLM provider and model settings are managed in `backend/llm_config.yaml`. The system uses two separate models: one for page analysis and test case generation, and one for test script generation.

```yaml
model_provider: "openai"  # Options: openai, groq, anthropic, etc.
model_settings:
  openai:
    analysis_model: "gpt-4o-2024-11-20"   # For page analysis and test generation
    selenium_model: "gpt-4.1-2025-04-14"  # For script generation
    temperature: 0.2
```

To switch providers, update `model_provider` to the desired provider name and add a corresponding block under `model_settings` following the same structure. Ensure the matching API key is set in the backend `.env` file.

---

## Contributing

Contributions, bug reports, and feature requests are welcome. Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to submit issues and pull requests.

---

## Future Scope and Improvements

- Continuous page analysis and test generation across authenticated sessions — automatically following login flows to cover protected pages.
- Support for additional testing frameworks and languages beyond Python Selenium and Playwright (for example, Cypress, Puppeteer, Java-based frameworks).
- Scheduled automated test execution with result aggregation and reporting dashboards within the web UI.
- AI-driven suggestions for improving web page content, accessibility, and SEO compliance.
- Externalised, user-editable LLM prompt templates through the web interface for enhanced prompt engineering without code changes.
- Expanded test suite builder capabilities including conditional branching logic, loop constructs, and parameterised test runs.
- Integration with CI/CD pipelines for triggering automated test generation and execution on deployment events.
- Multi-user support with role-based access control for team collaboration.

---

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.

---

## Acknowledgments

[Mindfire Digital LLP](https://www.mindfiresolutions.com/)
