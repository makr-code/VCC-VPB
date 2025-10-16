#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests für AIService.

Testet KI-gestützte Prozessgenerierung mit gemockten Ollama-Responses.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from vpb.services.ai_service import (
    AIService,
    AIConfig,
    AIResult,
    AIServiceError,
    OllamaConnectionError,
    ValidationError
)
from ollama_client import OllamaOptions


# ============================
# Fixtures
# ============================

@pytest.fixture
def ai_config():
    """Standard AI-Konfiguration für Tests."""
    return AIConfig(
        endpoint="http://localhost:11434",
        model="llama3.2:latest",
        temperature=0.7,
        num_predict=2048,
        max_examples=2,
        validation_tolerance="lenient"
    )


@pytest.fixture
def ai_service(ai_config):
    """AIService mit gemocktem OllamaClient."""
    with patch('vpb.services.ai_service.OllamaClient'):
        service = AIService(ai_config)
        return service


@pytest.fixture
def mock_ollama_client():
    """Mock OllamaClient."""
    client = Mock()
    client.health.return_value = {"models": [{"name": "llama3.2:latest"}]}
    return client


@pytest.fixture
def sample_process_json():
    """Beispiel-Prozess JSON für Tests."""
    return json.dumps({
        "metadata": {
            "name": "Testprozess",
            "description": "Ein Testprozess"
        },
        "elements": [
            {
                "element_id": "e1",
                "element_type": "StartEvent",
                "name": "Start",
                "x": 100,
                "y": 100,
                "description": "",
                "responsible_authority": "unbekannt",
                "legal_basis": "n.n.",
                "deadline_days": 0,
                "geo_reference": ""
            },
            {
                "element_id": "e2",
                "element_type": "Prozess",
                "name": "Task",
                "x": 300,
                "y": 100,
                "description": "",
                "responsible_authority": "unbekannt",
                "legal_basis": "n.n.",
                "deadline_days": 0,
                "geo_reference": ""
            }
        ],
        "connections": [
            {
                "connection_id": "c1",
                "connection_type": "SequenceFlow",
                "from_element": "e1",
                "to_element": "e2",
                "description": ""
            }
        ]
    })


@pytest.fixture
def mock_valid_process_response():
    """Gültige Prozess-Antwort vom KI-Modell."""
    return json.dumps({
        "metadata": {
            "name": "Genehmigungsprozess",
            "description": "Automatisch generiert"
        },
        "elements": [
            {
                "element_id": "e1",
                "element_type": "StartEvent",
                "name": "Antrag einreichen",
                "x": 100,
                "y": 100,
                "description": "Start des Prozesses",
                "responsible_authority": "Bürger",
                "legal_basis": "§1 TestG",
                "deadline_days": 0,
                "geo_reference": ""
            },
            {
                "element_id": "e2",
                "element_type": "Prozess",
                "name": "Antrag prüfen",
                "x": 300,
                "y": 100,
                "description": "Formale Prüfung",
                "responsible_authority": "Sachbearbeiter",
                "legal_basis": "§2 TestG",
                "deadline_days": 5,
                "geo_reference": ""
            },
            {
                "element_id": "e3",
                "element_type": "EndEvent",
                "name": "Abgeschlossen",
                "x": 500,
                "y": 100,
                "description": "",
                "responsible_authority": "unbekannt",
                "legal_basis": "n.n.",
                "deadline_days": 0,
                "geo_reference": ""
            }
        ],
        "connections": [
            {
                "connection_id": "c1",
                "connection_type": "SequenceFlow",
                "from_element": "e1",
                "to_element": "e2",
                "description": ""
            },
            {
                "connection_id": "c2",
                "connection_type": "SequenceFlow",
                "from_element": "e2",
                "to_element": "e3",
                "description": ""
            }
        ]
    })


# ============================
# AIService Initialization Tests
# ============================

class TestAIServiceInit:
    """Tests für AIService Initialisierung."""
    
    def test_init_with_defaults(self):
        """Test: Initialisierung mit Default-Konfiguration."""
        with patch('vpb.services.ai_service.OllamaClient'):
            service = AIService()
            assert service.config.endpoint == "http://localhost:11434"
            assert service.config.model == "llama3.2:latest"
            assert service.config.temperature == 0.7
    
    def test_init_with_custom_config(self, ai_config):
        """Test: Initialisierung mit Custom-Konfiguration."""
        with patch('vpb.services.ai_service.OllamaClient'):
            service = AIService(ai_config)
            assert service.config == ai_config
            assert service.config.max_examples == 2
    
    def test_repr(self, ai_service):
        """Test: __repr__ liefert aussagekräftige Darstellung."""
        repr_str = repr(ai_service)
        assert "AIService" in repr_str
        assert "llama3.2:latest" in repr_str
        assert "localhost" in repr_str


# ============================
# Health Check Tests
# ============================

class TestHealthCheck:
    """Tests für Ollama Health Check."""
    
    def test_health_check_success(self, ai_service, mock_ollama_client):
        """Test: Erfolgreicher Health Check."""
        ai_service.client = mock_ollama_client
        result = ai_service.health_check()
        
        assert "models" in result
        mock_ollama_client.health.assert_called_once()
    
    def test_health_check_failure(self, ai_service):
        """Test: Fehlgeschlagener Health Check."""
        ai_service.client.health.side_effect = Exception("Connection refused")
        
        with pytest.raises(OllamaConnectionError):
            ai_service.health_check()


# ============================
# Process Generation Tests
# ============================

class TestProcessGeneration:
    """Tests für Prozessgenerierung aus Text."""
    
    def test_generate_process_success(self, ai_service, mock_valid_process_response):
        """Test: Erfolgreiche Prozessgenerierung."""
        ai_service.client.generate.return_value = mock_valid_process_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.generate_process_from_text(
                "Ein Genehmigungsprozess mit Prüfung"
            )
            
            assert result.success
            assert len(result.get_elements()) == 3
            assert len(result.get_connections()) == 2
            assert result.get_metadata()["name"] == "Genehmigungsprozess"
    
    def test_generate_process_with_validation_issues(self, ai_service, mock_valid_process_response):
        """Test: Prozessgenerierung mit Validierungswarnungen."""
        ai_service.client.generate.return_value = mock_valid_process_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [
                    {"code": "WARN_MISSING_DESCRIPTION", "message": "Fehlende Description", "severity": "warning"}
                ],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.generate_process_from_text("Test")
            
            assert result.success
            assert len(result.validation_issues) == 1
            assert not result.fatal_errors
    
    def test_generate_process_fatal_error(self, ai_service):
        """Test: Prozessgenerierung mit fatalem Fehler."""
        ai_service.client.generate.return_value = '{"invalid": "json structure"}'
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": None,
                "issues": [{"code": "FATAL_INVALID_JSON", "message": "Invalid JSON", "severity": "fatal"}],
                "fatal": True,
                "repairs": []
            }
            
            result = ai_service.generate_process_from_text("Test")
            
            assert not result.success
            assert result.fatal_errors
    
    def test_generate_process_exception(self, ai_service):
        """Test: Exception während Prozessgenerierung."""
        ai_service.client.generate.side_effect = Exception("Network error")
        
        result = ai_service.generate_process_from_text("Test")
        
        assert not result.success
        assert "Network error" in result.message
    
    def test_generate_process_with_custom_options(self, ai_service, mock_valid_process_response):
        """Test: Prozessgenerierung mit Custom Ollama Options."""
        ai_service.client.generate.return_value = mock_valid_process_response
        
        custom_options = OllamaOptions(temperature=0.9, num_predict=4096)
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.generate_process_from_text(
                "Test",
                options=custom_options
            )
            
            assert result.success
            # Verify custom options were passed
            call_args = ai_service.client.generate.call_args
            assert call_args[1]['options'] == custom_options


# ============================
# Next Steps Tests
# ============================

class TestNextSteps:
    """Tests für Next Steps Vorschläge."""
    
    def test_suggest_next_steps_success(self, ai_service, sample_process_json):
        """Test: Erfolgreiche Next Steps Vorschläge."""
        next_steps_response = json.dumps({
            "elements": [
                {
                    "element_id": "e3",
                    "element_type": "Prozess",
                    "name": "Neuer Schritt",
                    "x": 500,
                    "y": 100,
                    "description": "",
                    "responsible_authority": "unbekannt",
                    "legal_basis": "n.n.",
                    "deadline_days": 0,
                    "geo_reference": ""
                }
            ],
            "connections": [
                {
                    "connection_id": "c2",
                    "connection_type": "SequenceFlow",
                    "from_element": "e2",
                    "to_element": "e3",
                    "description": ""
                }
            ]
        })
        
        ai_service.client.generate.return_value = next_steps_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(next_steps_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.suggest_next_steps(
                current_diagram_json=sample_process_json,
                selected_element_id="e2"
            )
            
            assert result.success
            assert len(result.get_elements()) == 1
            assert result.get_elements()[0]["element_id"] == "e3"
    
    def test_suggest_next_steps_no_selection(self, ai_service, sample_process_json):
        """Test: Next Steps ohne ausgewähltes Element."""
        ai_service.client.generate.return_value = '{"elements": [], "connections": []}'
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": {"elements": [], "connections": []},
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.suggest_next_steps(
                current_diagram_json=sample_process_json,
                selected_element_id=None
            )
            
            assert result.success
    
    def test_suggest_next_steps_exception(self, ai_service, sample_process_json):
        """Test: Exception bei Next Steps."""
        ai_service.client.generate.side_effect = Exception("Timeout")
        
        result = ai_service.suggest_next_steps(sample_process_json)
        
        assert not result.success
        assert "Timeout" in result.message


# ============================
# Diagnose & Fix Tests
# ============================

class TestDiagnoseAndFix:
    """Tests für Diagnose und Fix."""
    
    def test_diagnose_success(self, ai_service, sample_process_json):
        """Test: Erfolgreiche Diagnose."""
        diagnose_response = json.dumps({
            "issues": [
                {
                    "code": "MISSING_END_EVENT",
                    "message": "Prozess hat kein EndEvent",
                    "severity": "warning"
                }
            ],
            "patch": {
                "elements": [
                    {
                        "element_id": "e3",
                        "element_type": "EndEvent",
                        "name": "Ende",
                        "x": 500,
                        "y": 100,
                        "description": "",
                        "responsible_authority": "unbekannt",
                        "legal_basis": "n.n.",
                        "deadline_days": 0,
                        "geo_reference": ""
                    }
                ],
                "connections": []
            }
        })
        
        ai_service.client.generate.return_value = diagnose_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(diagnose_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.diagnose_and_fix(sample_process_json)
            
            assert result.success
            assert "issues" in result.data
            assert len(result.data["issues"]) == 1
            assert "patch" in result.data
    
    def test_diagnose_no_issues(self, ai_service, sample_process_json):
        """Test: Diagnose ohne gefundene Probleme."""
        diagnose_response = json.dumps({
            "issues": [],
            "patch": None
        })
        
        ai_service.client.generate.return_value = diagnose_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(diagnose_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.diagnose_and_fix(sample_process_json)
            
            assert result.success
            assert len(result.data["issues"]) == 0


# ============================
# Ingestion Tests
# ============================

class TestIngestion:
    """Tests für Ingestion aus externen Quellen."""
    
    def test_ingest_from_sources_success(self, ai_service):
        """Test: Erfolgreiche Ingestion."""
        sources = "Der Prozess beginnt mit einem Antrag..."
        
        ingestion_response = json.dumps({
            "elements": [
                {
                    "element_id": "e1",
                    "element_type": "StartEvent",
                    "name": "Antrag",
                    "x": 100,
                    "y": 100,
                    "description": "",
                    "responsible_authority": "unbekannt",
                    "legal_basis": "n.n.",
                    "deadline_days": 0,
                    "geo_reference": ""
                }
            ],
            "connections": []
        })
        
        ai_service.client.generate.return_value = ingestion_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(ingestion_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.ingest_from_sources(sources)
            
            assert result.success
            assert len(result.get_elements()) == 1
    
    def test_ingest_with_context(self, ai_service):
        """Test: Ingestion mit zusätzlichem Kontext."""
        result = ai_service.ingest_from_sources(
            sources_text="Text",
            prompt_context="Kontext: Baugenehmigung",
            current_diagram_summary="Bereits 5 Elemente vorhanden"
        )
        
        # Should not raise exception
        assert isinstance(result, AIResult)


# ============================
# Streaming Tests
# ============================

class TestStreaming:
    """Tests für Streaming-Operationen."""
    
    def test_generate_process_stream(self, ai_service):
        """Test: Prozessgenerierung im Streaming-Modus."""
        chunks = []
        
        def callback(chunk):
            chunks.append(chunk)
        
        # Mock stream generator
        ai_service.client.generate_stream.return_value = iter(["chunk1", "chunk2", "chunk3"])
        
        with patch('vpb.services.ai_service.build_prompt_with_examples_text_to_vpb') as mock_prompt:
            mock_prompt.return_value = ("prompt", Mock())
            
            job = ai_service.generate_process_stream(
                description="Test",
                callback=callback
            )
            
            assert job is not None
    
    def test_suggest_next_steps_stream(self, ai_service, sample_process_json):
        """Test: Next Steps im Streaming-Modus."""
        chunks = []
        
        def callback(chunk):
            chunks.append(chunk)
        
        ai_service.client.generate_stream.return_value = iter(["data"])
        
        with patch('vpb.services.ai_service.build_prompt_with_examples_next_steps') as mock_prompt:
            mock_prompt.return_value = ("prompt", Mock())
            
            job = ai_service.suggest_next_steps_stream(
                current_diagram_json=sample_process_json,
                selected_element_id="e1",
                callback=callback
            )
            
            assert job is not None


# ============================
# Validation Tests
# ============================

class TestValidation:
    """Tests für Validierung."""
    
    def test_validate_output_success(self, ai_service, mock_valid_process_response):
        """Test: Erfolgreiche Validierung."""
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result = ai_service.validate_output(
                raw_output=mock_valid_process_response,
                mode="text_to_vpb",
                existing_ids=[]
            )
            
            assert result["parsed"] is not None
            assert not result["fatal"]
    
    def test_validate_output_with_existing_ids(self, ai_service):
        """Test: Validierung mit existierenden IDs."""
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": {},
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            ai_service.validate_output(
                raw_output='{}',
                mode="next_steps",
                existing_ids=["e1", "e2"]
            )
            
            # Verify existing_ids were passed
            call_args = mock_validate.call_args
            assert "e1" in call_args[1]["existing_ids"]


# ============================
# AIResult Tests
# ============================

class TestAIResult:
    """Tests für AIResult Klasse."""
    
    def test_result_success(self):
        """Test: Erfolgreiches Result ist truthy."""
        result = AIResult(success=True, data={"elements": []})
        assert bool(result) is True
    
    def test_result_failure(self):
        """Test: Fehlgeschlagenes Result ist falsy."""
        result = AIResult(success=False)
        assert bool(result) is False
    
    def test_result_with_fatal_errors(self):
        """Test: Result mit fatalen Fehlern ist falsy."""
        result = AIResult(success=True, fatal_errors=True)
        assert bool(result) is False
    
    def test_get_elements(self):
        """Test: Extrahieren von Elements."""
        data = {
            "elements": [{"element_id": "e1"}, {"element_id": "e2"}],
            "connections": []
        }
        result = AIResult(success=True, data=data)
        elements = result.get_elements()
        
        assert len(elements) == 2
        assert elements[0]["element_id"] == "e1"
    
    def test_get_elements_empty(self):
        """Test: Leere Elements-Liste."""
        result = AIResult(success=True, data={})
        elements = result.get_elements()
        assert elements == []
    
    def test_get_connections(self):
        """Test: Extrahieren von Connections."""
        data = {
            "elements": [],
            "connections": [{"connection_id": "c1"}]
        }
        result = AIResult(success=True, data=data)
        connections = result.get_connections()
        
        assert len(connections) == 1
        assert connections[0]["connection_id"] == "c1"
    
    def test_get_metadata(self):
        """Test: Extrahieren von Metadata."""
        data = {
            "metadata": {"name": "Test", "description": "Desc"},
            "elements": []
        }
        result = AIResult(success=True, data=data)
        metadata = result.get_metadata()
        
        assert metadata["name"] == "Test"
        assert metadata["description"] == "Desc"
    
    def test_get_metadata_none(self):
        """Test: Keine Metadata vorhanden."""
        result = AIResult(success=True, data={"elements": []})
        metadata = result.get_metadata()
        assert metadata is None


# ============================
# AIConfig Tests
# ============================

class TestAIConfig:
    """Tests für AIConfig."""
    
    def test_config_defaults(self):
        """Test: Default-Werte."""
        config = AIConfig()
        assert config.endpoint == "http://localhost:11434"
        assert config.model == "llama3.2:latest"
        assert config.temperature == 0.7
        assert config.num_predict == 2048
        assert config.max_examples == 3
        assert config.validation_tolerance == "strict"
    
    def test_config_custom_values(self):
        """Test: Custom-Werte."""
        config = AIConfig(
            endpoint="http://custom:11434",
            model="custom-model",
            temperature=0.9,
            max_examples=5
        )
        assert config.endpoint == "http://custom:11434"
        assert config.model == "custom-model"
        assert config.temperature == 0.9
        assert config.max_examples == 5
    
    def test_config_element_types(self):
        """Test: Element-Types."""
        config = AIConfig()
        assert "StartEvent" in config.element_types
        assert "Prozess" in config.element_types
        assert "EndEvent" in config.element_types
    
    def test_config_connection_types(self):
        """Test: Connection-Types."""
        config = AIConfig()
        assert "SequenceFlow" in config.connection_types
        assert "DataFlow" in config.connection_types


# ============================
# Integration Tests
# ============================

class TestAIServiceIntegration:
    """Integration-Tests für AIService."""
    
    def test_full_workflow_generate_and_validate(self, ai_service, mock_valid_process_response):
        """Test: Kompletter Workflow von Generation bis Validierung."""
        ai_service.client.generate.return_value = mock_valid_process_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            # Generate
            result = ai_service.generate_process_from_text("Ein Prozess")
            assert result.success
            
            # Validate separately
            validation = ai_service.validate_output(
                raw_output=result.raw_output,
                mode="text_to_vpb"
            )
            assert validation["parsed"] is not None
    
    def test_chained_operations(self, ai_service, mock_valid_process_response, sample_process_json):
        """Test: Verkettete Operationen."""
        # First generate
        ai_service.client.generate.return_value = mock_valid_process_response
        
        with patch('vpb.services.ai_service.validate_model_output') as mock_validate:
            mock_validate.return_value = {
                "parsed": json.loads(mock_valid_process_response),
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result1 = ai_service.generate_process_from_text("Initial")
            assert result1.success
            
            # Then suggest next steps
            next_response = '{"elements": [], "connections": []}'
            ai_service.client.generate.return_value = next_response
            mock_validate.return_value = {
                "parsed": {"elements": [], "connections": []},
                "issues": [],
                "fatal": False,
                "repairs": []
            }
            
            result2 = ai_service.suggest_next_steps(sample_process_json)
            assert result2.success
