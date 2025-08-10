import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for AI generator tests."""
    mock_client = Mock()
    mock_messages = Mock()
    
    mock_response = Mock()
    mock_response.content = [
        Mock(
            type="text",
            text="This is a test response"
        )
    ]
    
    mock_messages.create = Mock(return_value=mock_response)
    mock_client.messages = mock_messages
    
    return mock_client

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing."""
    mock_store = Mock()
    
    mock_store.search = Mock(return_value=[
        {
            "content": "Test content from course",
            "metadata": {
                "course_title": "Test Course",
                "lesson_number": 1,
                "chunk_index": 0
            }
        }
    ])
    
    mock_store.get_all_courses = Mock(return_value=[
        {"title": "Test Course 1", "instructor": "Test Instructor 1", "link": "http://test1.com"},
        {"title": "Test Course 2", "instructor": "Test Instructor 2", "link": "http://test2.com"}
    ])
    
    mock_store.resolve_course_name = Mock(return_value="Test Course")
    
    return mock_store

@pytest.fixture
def mock_ai_generator():
    """Mock AIGenerator for testing."""
    mock_gen = AsyncMock()
    mock_gen.generate = AsyncMock(return_value={
        "response": "This is a test response",
        "sources": []
    })
    return mock_gen

@pytest.fixture
def mock_session_manager():
    """Mock SessionManager for testing."""
    mock_manager = Mock()
    mock_manager.get_or_create_session = Mock(return_value="test-session-id")
    mock_manager.add_message = Mock()
    mock_manager.get_history = Mock(return_value=[])
    return mock_manager

@pytest.fixture
def mock_rag_system(mock_vector_store, mock_ai_generator, mock_session_manager):
    """Mock RAGSystem for testing."""
    with patch('rag_system.VectorStore', return_value=mock_vector_store), \
         patch('rag_system.AIGenerator', return_value=mock_ai_generator), \
         patch('rag_system.SessionManager', return_value=mock_session_manager):
        
        from rag_system import RAGSystem
        rag_system = RAGSystem()
        rag_system.vector_store = mock_vector_store
        rag_system.ai_generator = mock_ai_generator
        rag_system.session_manager = mock_session_manager
        
        return rag_system

@pytest.fixture
def sample_query_request():
    """Sample query request data."""
    return {
        "query": "What is deep learning?",
        "session_id": "test-session-123"
    }

@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return [
        {
            "title": "Introduction to Deep Learning",
            "instructor": "Andrew Ng",
            "link": "https://example.com/course1"
        },
        {
            "title": "Advanced Machine Learning",
            "instructor": "Jane Doe",
            "link": "https://example.com/course2"
        }
    ]

@pytest.fixture
def mock_course_search_tool():
    """Mock CourseSearchTool for testing."""
    mock_tool = Mock()
    mock_tool.execute = Mock(return_value={
        "results": [
            {
                "content": "Deep learning is a subset of machine learning",
                "course": "Introduction to Deep Learning",
                "lesson": 1
            }
        ]
    })
    mock_tool.last_sources = [
        {
            "course": "Introduction to Deep Learning",
            "lesson": 1
        }
    ]
    return mock_tool

@pytest.fixture
def test_app_client():
    """Create a test client for the FastAPI app without static file mounting."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from pydantic import BaseModel, Field
    from typing import Optional
    
    class QueryRequest(BaseModel):
        query: str = Field(..., min_length=1)
        session_id: Optional[str] = None
    
    class QueryResponse(BaseModel):
        response: str
        session_id: str
        sources: List[Dict[str, Any]]
    
    app = FastAPI()
    
    mock_rag = Mock()
    mock_rag.process_query = AsyncMock(return_value={
        "response": "Test response",
        "sources": []
    })
    mock_rag.vector_store = Mock()
    mock_rag.vector_store.get_all_courses = Mock(return_value=[
        {"title": "Test Course", "instructor": "Test Instructor", "link": "http://test.com"}
    ])
    
    @app.get("/")
    async def root():
        return {"message": "DeepLearning.AI Course Assistant API"}
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query(request: QueryRequest):
        try:
            result = await mock_rag.process_query(
                query=request.query,
                session_id=request.session_id
            )
            
            return QueryResponse(
                response=result["response"],
                session_id=request.session_id or "test-session",
                sources=result.get("sources", [])
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses")
    async def get_courses():
        try:
            courses = mock_rag.vector_store.get_all_courses()
            return {"courses": courses}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    client = TestClient(app)
    client.mock_rag = mock_rag
    
    return client