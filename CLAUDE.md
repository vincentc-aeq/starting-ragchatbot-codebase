# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) chatbot system for answering questions about DeepLearning.AI course materials. It uses semantic search with ChromaDB and Anthropic's Claude for intelligent response generation.

## Development Commands

```bash
# Install dependencies
uv sync

# Run application (quick start)
./run.sh

# Run application (manual)
cd backend && uv run uvicorn app:app --reload --port 8000

# Environment setup - Required before running
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

**Access Points:**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture Overview

### Core Data Flow
```
User Query → Frontend → FastAPI → RAGSystem → AIGenerator → Claude API
                                                    ↓
                                            Tool Decision (search or direct)
                                                    ↓
                                    CourseSearchTool → VectorStore → ChromaDB
                                                    ↓
                                            Response Synthesis → User
```

### Key Architectural Decisions

1. **Tool-Calling Pattern**: AI decides whether to search course content or answer directly. Single search per query for performance.

2. **Dual Vector Collections**:
   - `course_catalog`: Course metadata for smart name resolution
   - `course_content`: Chunked content with embeddings

3. **Sentence-Based Chunking**: 800 chars with 100 char overlap, preserving semantic boundaries

4. **Session Management**: In-memory conversation tracking with configurable history limits

### Component Responsibilities

- **`app.py`**: FastAPI endpoints, CORS, static file serving
- **`rag_system.py`**: Orchestrates query processing, manages tools and sessions
- **`ai_generator.py`**: Claude API integration, tool execution, response generation
- **`vector_store.py`**: ChromaDB interface, semantic search, course resolution
- **`search_tools.py`**: Tool interface and CourseSearchTool implementation
- **`document_processor.py`**: Text chunking, course structure extraction
- **`session_manager.py`**: Conversation history management
- **`config.py`**: Centralized configuration with environment variables

### Frontend Integration

- Pure HTML/CSS/JavaScript (no framework)
- Real-time chat interface with markdown support
- Session persistence for conversation context
- Collapsible source citations

## Critical Implementation Notes

### Document Processing Pipeline
1. Reads course files from `/docs` folder on startup
2. Extracts metadata (title, instructor, link) from first 3 lines
3. Identifies lessons with pattern: `Lesson N: Title`
4. Creates searchable chunks with course/lesson context

### Search Behavior
- Course name matching uses semantic similarity (partial names work)
- Lesson filtering supports specific lesson queries
- Results include course title and lesson number for context
- Sources tracked and displayed in UI

### AI System Prompt
Located in `ai_generator.py:SYSTEM_PROMPT`. Instructs Claude to:
- Use search only for course-specific questions
- Limit to one search per query
- Provide concise, educational responses
- Avoid meta-commentary about search process

### Error Handling
- Vector search failures return graceful error messages
- Empty search results handled with clear feedback
- Session creation automatic if not provided
- API errors return HTTPException with status codes

## Dependencies

Core packages (from `pyproject.toml`):
- `chromadb==1.0.15` - Vector database
- `anthropic==0.58.2` - Claude AI
- `sentence-transformers==5.0.0` - Embeddings
- `fastapi==0.116.1` - Web framework
- `uvicorn==0.35.0` - ASGI server
- `python-dotenv==1.1.1` - Environment variables

## Common Tasks

### Adding New Course Documents
1. Place `.txt` files in `/docs` folder
2. Follow format: Course Title, Course Link, Instructor, then content
3. Restart server to index new documents

### Modifying Search Behavior
- Adjust chunk size/overlap in `config.py`
- Modify embedding model in `config.py` (default: all-MiniLM-L6-v2)
- Change max search results in `vector_store.py`

### Debugging Query Flow
1. Check browser console for frontend errors
2. View API logs in terminal for backend issues
3. FastAPI docs at `/docs` for testing endpoints directly
4. Search results tracked in `search_tools.py:last_sources`

## Performance Characteristics
- Vector search: ~100-200ms
- Claude API: ~1-3s
- Total query: ~2-5s
- Chunk size: 800 chars (configurable)
- History limit: 10 messages (configurable)
- always use uv to run the server do not use pip directly
- make sure to use uv to manage all dependencies