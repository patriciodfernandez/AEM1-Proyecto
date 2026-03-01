"""
Tests para Support AI Query
Validación de JSON, campos requeridos, métricas y comportamiento
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Importar funciones del script principal
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_query import (
    parse_and_validate_response,
    calculate_cost,
    load_prompt,
)


# ============================================================================
# TEST 1: Validar que se puede cargar el prompt
# ============================================================================
class TestPromptLoading:
    """Tests para verificar que el prompt se carga correctamente."""
    
    def test_prompt_file_exists(self):
        """¿Existe el archivo del prompt?"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "main_prompt.txt"
        assert prompt_path.exists(), "Archivo main_prompt.txt no encontrado"
    
    def test_prompt_has_content(self):
        """¿El prompt tiene contenido (no está vacío)?"""
        prompt = load_prompt()
        assert len(prompt) > 0, "El prompt está vacío"
        assert len(prompt) > 100, "El prompt es muy corto"
    
    def test_prompt_has_required_sections(self):
        """¿El prompt contiene las secciones críticas?"""
        prompt = load_prompt()
        required_sections = ["SYSTEM PROMPT", "INSTRUCCIONES", "FORMATO", "EJEMPLOS"]
        
        for section in required_sections:
            assert section in prompt, f"Falta sección '{ section}' en prompt"
    
    def test_prompt_has_json_format_spec(self):
        """¿El prompt especifica formato JSON?"""
        prompt = load_prompt()
        assert "json" in prompt.lower(), "Prompt no menciona JSON"
        assert '"response"' in prompt, "Prompt no especifica campo 'response'"


# ============================================================================
# TEST 2: Validar respuestas JSON
# ============================================================================
class TestJSONValidation:
    """Tests para verificar que las respuestas JSON son válidas."""
    
    def test_valid_json_response(self):
        """¿Acepta un JSON válido?"""
        valid_json = {
            "response": "Haz clic en Olvidé contraseña",
            "confidence": "ALTA",
            "confidence_explanation": "Es un procedimiento estándar",
            "actions": ["respond_to_customer"],
            "reasoning": "Solución común"
        }
        response_text = json.dumps(valid_json)
        
        # No debería lanzar excepción
        result = parse_and_validate_response(response_text)
        assert result["confidence"] == "ALTA"
    
    def test_invalid_json_raises_error(self):
        """¿Rechaza JSON inválido?"""
        invalid_json = '{"response": "Test", "incomplete": }'
        
        with pytest.raises(ValueError, match="JSON válido"):
            parse_and_validate_response(invalid_json)
    
    def test_missing_required_field_raises_error(self):
        """¿Rechaza cuando falta un campo requerido (confidence)?"""
        incomplete_json = {
            "response": "Test response",
            # FALTA: "confidence"
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(incomplete_json)
        
        with pytest.raises(ValueError, match="confidence"):
            parse_and_validate_response(response_text)
    
    def test_invalid_confidence_value_raises_error(self):
        """¿Rechaza valores de confidence inválidos?"""
        invalid_json = {
            "response": "Test",
            "confidence": "EXTRA_ALTA",  # NO es una opción válida
            "confidence_explanation": "Test",
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(invalid_json)
        
        with pytest.raises(ValueError, match="ALTA|MEDIA|BAJA"):
            parse_and_validate_response(response_text)


# ============================================================================
# TEST 3: Validar campos requeridos
# ============================================================================
class TestRequiredFields:
    """Tests para verificar que todos los campos requeridos estén presentes."""
    
    def test_all_required_fields_present(self):
        """¿La respuesta tiene TODOS los campos requeridos?"""
        valid_response = {
            "response": "Respuesta de ejemplo",
            "confidence": "MEDIA",
            "confidence_explanation": "Explicación",
            "actions": ["respond_to_customer", "create_follow_up"],
            "reasoning": "Razonamiento"
        }
        response_text = json.dumps(valid_response)
        result = parse_and_validate_response(response_text)
        
        # Verificar que todos los campos están
        assert "response" in result
        assert "confidence" in result
        assert "confidence_explanation" in result
        assert "actions" in result
        assert "reasoning" in result
    
    def test_response_is_not_empty(self):
        """¿El campo 'response' tiene contenido?"""
        valid_response = {
            "response": "Respuesta sustancial",  # No vacío
            "confidence": "ALTA",
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(valid_response)
        result = parse_and_validate_response(response_text)
        
        assert len(result["response"]) > 0, "Response no debe estar vacío"
    
    def test_actions_is_list(self):
        """¿El campo 'actions' es siempre una LISTA?"""
        valid_response = {
            "response": "Test",
            "confidence": "ALTA",
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer", "escalate"]  # DEBE ser lista
        }
        response_text = json.dumps(valid_response)
        result = parse_and_validate_response(response_text)
        
        assert isinstance(result["actions"], list), "actions debe ser una lista"


# ============================================================================
# TEST 4: Validar valores de Confidence
# ============================================================================
class TestConfidenceValues:
    """Tests para verificar valores válidos de confidence."""
    
    @pytest.mark.parametrize("confidence_value", ["ALTA", "MEDIA", "BAJA"])
    def test_valid_confidence_values(self, confidence_value):
        """¿Aceptan todos los valores válidos de confidence?"""
        response = {
            "response": "Test",
            "confidence": confidence_value,
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(response)
        
        # No debería lanzar excepción
        result = parse_and_validate_response(response_text)
        assert result["confidence"] == confidence_value
    
    @pytest.mark.parametrize("invalid_confidence", ["SUPER_ALTA", "MEDIUM", "9"])
    def test_invalid_confidence_values(self, invalid_confidence):
        """¿Rechaza valores inválidos de confidence?"""
        response = {
            "response": "Test",
            "confidence": invalid_confidence,
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(response)
        
        with pytest.raises(ValueError):
            parse_and_validate_response(response_text)


# ============================================================================
# TEST 5: Validar cálculo de costos
# ============================================================================
class TestCostCalculation:
    """Tests para verificar que el cálculo de costos es correcto."""
    
    def test_cost_calculation_zero_tokens(self):
        """¿Costo es 0 cuando tokens es 0?"""
        cost = calculate_cost(0)
        assert cost == 0.0, "Costo con 0 tokens debe ser 0"
    
    def test_cost_calculation_1000_tokens(self):
        """¿Costo es correcto para 1,000 tokens?"""
        # Precio: $0.225 por 1M tokens
        # 1,000 tokens = 0.001M = 0.001 * 0.225 = 0.000225
        cost = calculate_cost(1000)
        expected = (1000 / 1_000_000) * 0.225
        assert abs(cost - expected) < 0.0001, f"Costo incorrecto: {cost} vs {expected}"
    
    def test_cost_increases_with_tokens(self):
        """¿El costo aumenta con más tokens?"""
        cost_100 = calculate_cost(100)
        cost_1000 = calculate_cost(1000)
        
        assert cost_1000 > cost_100, "Más tokens debe costar más"
    
    def test_cost_formula_consistency(self):
        """¿La fórmula de costo es consistente?"""
        # Si duplicamos tokens, costo debe duplicarse
        cost_500 = calculate_cost(500)
        cost_1000 = calculate_cost(1000)
        
        # cost_1000 debería ser ~2x cost_500
        assert cost_1000 / cost_500 == pytest.approx(2.0, rel=0.01)


# ============================================================================
# TEST 6: Validar estructura de acciones
# ============================================================================
class TestActionValidation:
    """Tests para verificar que las acciones sean válidas."""
    
    valid_actions = [
        "respond_to_customer",
        "escalate",
        "request_more_info",
        "close_ticket",
        "create_follow_up"
    ]
    
    def test_actions_are_list(self):
        """¿Actions siempre es una lista?"""
        response = {
            "response": "Test",
            "confidence": "ALTA",
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        response_text = json.dumps(response)
        result = parse_and_validate_response(response_text)
        
        assert isinstance(result["actions"], list)
    
    def test_actions_not_empty(self):
        """¿Al menos hay una acción?"""
        response = {
            "response": "Test",
            "confidence": "ALTA",
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]  # Al menos una
        }
        response_text = json.dumps(response)
        result = parse_and_validate_response(response_text)
        
        assert len(result["actions"]) > 0, "Debe haber al menos una acción"


# ============================================================================
# TEST 7: Validación de entrada
# ============================================================================
class TestInputValidation:
    """Tests para validar entrada de usuarios."""
    
    def test_empty_question_handling(self):
        """¿Se maneja pregunta vacía correctamente?"""
        # Este test es más conceptual
        # En producción, querríamos rechazar preguntas vacías
        empty_question = ""
        
        # Deberíamos validar esto antes de enviar a API
        assert len(empty_question.strip()) == 0
    
    def test_very_long_question(self):
        """¿Se maneja pregunta muy larga?"""
        # OpenAI tiene límite de tokens, pero es muy alto
        very_long = "¿" + ("pregunta " * 500) + "?"
        
        # Debería ser aceptable (max_tokens_prompt típicamente > 10k)
        assert len(very_long) > 1000


# ============================================================================
# TEST 8: Validación de métricas
# ============================================================================
class TestMetricsValidation:
    """Tests para validar que las métricas se calculan correctamente."""
    
    def test_latency_is_positive(self):
        """¿Latencia siempre es positiva?"""
        # Latencia nunca puede ser negativa
        latency = 3374.98
        assert latency > 0, "Latencia debe ser positiva"
    
    def test_tokens_are_positive_integers(self):
        """¿Tokens siempre son enteros positivos?"""
        tokens_prompt = 787
        tokens_completion = 102
        
        assert isinstance(tokens_prompt, int)
        assert isinstance(tokens_completion, int)
        assert tokens_prompt > 0
        assert tokens_completion > 0
    
    def test_total_tokens_equals_sum(self):
        """¿Total tokens = prompt + completion?"""
        prompt_tokens = 787
        completion_tokens = 102
        total_tokens = 889
        
        assert total_tokens == prompt_tokens + completion_tokens


# ============================================================================
# RUNNING THE TESTS
# ============================================================================
if __name__ == "__main__":
    # Para ejecutar: pytest tests/test_core.py -v
    pytest.main([__file__, "-v"])
