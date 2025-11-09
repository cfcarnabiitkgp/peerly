# Project: Agentic co-reviewing assistant for technical manuscript writing

Peerly is a web-based multi-agentic LLM web application system co-reviewing technical research paper contents. Built with FastAPI, LangGraph, React (Vite), and Qdrant, this application provides Grammarly-style suggestions tailored for academic research writing in mathematics, computer science, and related domains.

As the user writes LaTex code in different sections (e.g. Introduction, Methodology, Experimental Validation etc.), the LLM should provide guidelines/suggestions on how to improve the text.

Key features include:

- **Real-time Peer Review**: Get instant, targeted feedback on your research paper as you write
- **LangGraph Workflow**: StateGraph-based orchestration with Pydantic BaseModel state management
  - **Clarity Agent**: Identifies unclear statements, complex sentences, and undefined jargon
  - **Rigor Agent**: Validates experimental and mathematical rigor, statistical appropriateness, and assumptions
  - **Orchestrator Validation**: Final validation, prioritization, and cross-checking of suggestions
  - **Section-wise Analysis**: Each section analyzed independently for focused feedback
  - **Fast & Efficient**: 5-10 seconds for typical papers with optimized token usage
- **Split-View Interface**: Write in Markdown on the left, view suggestions on the right
- **Severity Levels**: Color-coded suggestions (Info, Warning, Error)
- **Filterable Suggestions**: Filter by type and severity for focused review


There will be a RAG component where some technical guidelines, paper writing best practices etc. will be available for the agents to make reasonable suggestions.

# Technology Stack

- FastAPI for backend (in `/app` directory)
- React + Vite for frontend (in `/frontend` directory)
- Tailwind CSS for styling
- LangGraph for agent orchestration for LLM applications
- Qdrant for vector databases


# Guidelines

- Structure: /app with /routers, /services, /models, /agents
- Use OOP and SOLID patterns in Python with clear separations of boundaries and concerns
- Use FastAPI's dependency injection for database and services
- Implement WebSocket endpoints for streaming LLM responses (when appropriate)
- Use Pydantic v2 for request/response validation
- Create LangGraph graphs for agentic workflows
- Implement proper RAG pipeline: embedding → vector store → retrieval → generation
- Use async/await operations when appropriate for efficiency reasons
- Add middleware for CORS, authentication, rate limiting
- Implement tool schemas with proper input validation
- Implement proper error handling like high-grade production level Python code
- Use environment variables for all API keys and configs
- Use Pydantic v2 and its BaseSettings class to manage application configurations
- Configuration data should not be committed to git unless otherwise forced by user
- Follow consistent naming: camelCase (TS), snake_case (Python) and follow good PEP conventions
- Add type hints in Python
- Keep components/functions small and single-purpose (separation of responsibility)
- Use docstrings for python and class definitions and follow PEP 8 conventions
- Use Python classes and OOP design principles when appropriate  
- code should be extensible when I want to add other LLM agents 
- I will use OpenAI models for now (but it should be easy to switch to anthropic models too) within LangGraph

# Project Structure

```
Peerly-Demo/
├── app/                    # FastAPI backend
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   ├── models/            # Pydantic models
│   ├── agents/            # LangGraph agents
│   ├── config/            # Configuration
│   └── rag/               # RAG pipeline
├── frontend/              # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx       # Main app component
│   │   ├── LatexEditor.jsx
│   │   └── SuggestionsPanel.jsx
│   └── .env              # Frontend environment variables
└── rag_resources/        # RAG knowledge base
```

# Other Guidelines

- Always use the tests folder for your debugging and testing codes
- The `/frontend` directory contains the React application with an Overleaf-style LaTeX editor interface
- Use the AIE8-certification-challenge repository in Desktop folder of this machine for preliminary understanding of previous work (but dont copy all of its implementations)
- Backend runs on port 8000 by default, frontend on port 5173 (Vite dev server)