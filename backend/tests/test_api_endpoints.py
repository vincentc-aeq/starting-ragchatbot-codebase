import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

class TestAPIEndpoints:
    """Test suite for FastAPI endpoints."""
    
    def test_root_endpoint(self, test_app_client):
        """Test the root endpoint returns correct message."""
        response = test_app_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "DeepLearning.AI Course Assistant API"
    
    def test_query_endpoint_success(self, test_app_client):
        """Test successful query processing."""
        request_data = {
            "query": "What is deep learning?",
            "session_id": "test-session-123"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "Deep learning is a subset of machine learning that uses neural networks.",
            "sources": [
                {
                    "course": "Introduction to Deep Learning",
                    "lesson": 1
                }
            ]
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        assert "sources" in data
        assert data["session_id"] == "test-session-123"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["course"] == "Introduction to Deep Learning"
    
    def test_query_endpoint_without_session(self, test_app_client):
        """Test query without session_id."""
        request_data = {
            "query": "Explain neural networks"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "Neural networks are computational models inspired by the human brain.",
            "sources": []
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session"
    
    def test_query_endpoint_empty_query(self, test_app_client):
        """Test query with empty string."""
        request_data = {
            "query": ""
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code in [422, 400]
    
    def test_query_endpoint_error_handling(self, test_app_client):
        """Test error handling in query endpoint."""
        request_data = {
            "query": "What is deep learning?"
        }
        
        test_app_client.mock_rag.process_query.side_effect = Exception("Processing error")
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Processing error" in data["detail"]
    
    def test_courses_endpoint_success(self, test_app_client):
        """Test successful course listing."""
        test_app_client.mock_rag.vector_store.get_all_courses.return_value = [
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
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "courses" in data
        assert len(data["courses"]) == 2
        assert data["courses"][0]["title"] == "Introduction to Deep Learning"
        assert data["courses"][1]["instructor"] == "Jane Doe"
    
    def test_courses_endpoint_empty_list(self, test_app_client):
        """Test courses endpoint with no courses."""
        test_app_client.mock_rag.vector_store.get_all_courses.return_value = []
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "courses" in data
        assert data["courses"] == []
    
    def test_courses_endpoint_error_handling(self, test_app_client):
        """Test error handling in courses endpoint."""
        test_app_client.mock_rag.vector_store.get_all_courses.side_effect = Exception("Database error")
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database error" in data["detail"]


class TestQueryValidation:
    """Test query validation and edge cases."""
    
    def test_query_with_special_characters(self, test_app_client):
        """Test query with special characters."""
        request_data = {
            "query": "What is @#$% in ML?",
            "session_id": "test-123"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "I can help with that.",
            "sources": []
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
    
    def test_query_with_long_text(self, test_app_client):
        """Test query with very long text."""
        long_query = "a" * 5000
        request_data = {
            "query": long_query,
            "session_id": "test-123"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "Response to long query",
            "sources": []
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
    
    def test_query_with_unicode(self, test_app_client):
        """Test query with unicode characters."""
        request_data = {
            "query": "什么是深度学习？",
            "session_id": "test-123"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "Deep learning in Chinese context",
            "sources": []
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestResponseFormat:
    """Test response format and structure."""
    
    def test_query_response_structure(self, test_app_client):
        """Test that query response has correct structure."""
        request_data = {
            "query": "Test query",
            "session_id": "test-123"
        }
        
        test_app_client.mock_rag.process_query.return_value = {
            "response": "Test response",
            "sources": [
                {"course": "Course 1", "lesson": 1},
                {"course": "Course 2", "lesson": 2}
            ]
        }
        
        response = test_app_client.post(
            "/api/query",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert isinstance(data["response"], str)
        assert isinstance(data["session_id"], str)
        assert isinstance(data["sources"], list)
        
        for source in data["sources"]:
            assert isinstance(source, dict)
            assert "course" in source
            assert "lesson" in source
    
    def test_courses_response_structure(self, test_app_client):
        """Test that courses response has correct structure."""
        test_app_client.mock_rag.vector_store.get_all_courses.return_value = [
            {
                "title": "Course 1",
                "instructor": "Instructor 1",
                "link": "http://link1.com"
            }
        ]
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert isinstance(data["courses"], list)
        
        for course in data["courses"]:
            assert isinstance(course, dict)
            assert "title" in course
            assert "instructor" in course
            assert "link" in course