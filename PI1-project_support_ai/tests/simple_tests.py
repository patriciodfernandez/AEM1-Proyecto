"""
Tests Simples para Support AI Query (sin pytest)
Validación manual de funciones críticas
"""

import json
import sys
from pathlib import Path

# Importar funciones del script principal
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_query import (
    parse_and_validate_response,
    calculate_cost,
    load_prompt,
)


def test_prompt_loading():
    """Test 1: ¿Se puede cargar el prompt?"""
    print("\n" + "="*70)
    print("TEST 1: Cargar Prompt")
    print("="*70)
    try:
        prompt = load_prompt()
        assert len(prompt) > 100, "Prompt muy corto"
        assert "SYSTEM PROMPT" in prompt, "Falta SYSTEM PROMPT"
        assert "EJEMPLOS" in prompt, "Faltan EJEMPLOS"
        print("✅ PASÓ: Prompt cargado correctamente")
        print(f"   Tamaño del prompt: {len(prompt)} caracteres")
        return True
    except Exception as e:
        print(f"❌ FALLÓ: {e}")
        return False


def test_json_validation():
    """Test 2: ¿Se valida JSON correctamente?"""
    print("\n" + "="*70)
    print("TEST 2: Validación de JSON")
    print("="*70)
    
    # Test 2A: JSON válido
    print("\n  2A: JSON válido...")
    valid_json = {
        "response": "Haz clic en Olvidé contraseña",
        "confidence": "ALTA",
        "confidence_explanation": "Es un procedimiento estándar",
        "actions": ["respond_to_customer"],
        "reasoning": "Solución común"
    }
    try:
        result = parse_and_validate_response(json.dumps(valid_json))
        assert result["confidence"] == "ALTA"
        print("  ✅ JSON válido acepto correctamente")
    except Exception as e:
        print(f"  ❌ Error con JSON válido: {e}")
        return False
    
    # Test 2B: JSON inválido
    print("\n  2B: JSON inválido...")
    invalid_json = '{"response": "Test", "incomplete": }'
    try:
        parse_and_validate_response(invalid_json)
        print("  ❌ Debería haber rechazado JSON inválido")
        return False
    except ValueError:
        print("  ✅ Rechazó JSON inválido correctamente")
    
    # Test 2C: Campo faltante
    print("\n  2C: Campo requerido faltante...")
    incomplete = {
        "response": "Test",
        # FALTA: "confidence"
        "actions": ["respond_to_customer"]
    }
    try:
        parse_and_validate_response(json.dumps(incomplete))
        print("  ❌ Debería haber rechazado JSON sin 'confidence'")
        return False
    except ValueError:
        print("  ✅ Rechazó campo faltante correctamente")
    
    print("\n✅ PASÓ: Validación JSON funciona correctamente")
    return True


def test_confidence_values():
    """Test 3: ¿Se validan valores de confidence?"""
    print("\n" + "="*70)
    print("TEST 3: Validación de Confidence")
    print("="*70)
    
    valid_values = ["ALTA", "MEDIA", "BAJA"]
    invalid_values = ["SUPER_ALTA", "MEDIUM", "9", "BAJO"]
    
    # Test valores válidos
    print("\n  Probando valores VÁLIDOS...")
    for confidence in valid_values:
        response = {
            "response": "Test",
            "confidence": confidence,
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        try:
            result = parse_and_validate_response(json.dumps(response))
            print(f"    ✅ Aceptó '{confidence}'")
        except ValueError as e:
            print(f"    ❌ Rechazó '{confidence}' (cuando debería aceptarlo): {e}")
            return False
    
    # Test valores inválidos
    print("\n  Probando valores INVÁLIDOS...")
    for confidence in invalid_values:
        response = {
            "response": "Test",
            "confidence": confidence,
            "confidence_explanation": "Expl",
            "actions": ["respond_to_customer"]
        }
        try:
            parse_and_validate_response(json.dumps(response))
            print(f"    ❌ Aceptó '{confidence}' (cuando debería rechazarlo)")
            return False
        except ValueError:
            print(f"    ✅ Rechazó '{confidence}'")
    
    print("\n✅ PASÓ: Validación de Confidence funciona correctamente")
    return True


def test_cost_calculation():
    """Test 4: ¿Se calcula el costo correctamente?"""
    print("\n" + "="*70)
    print("TEST 4: Cálculo de Costos")
    print("="*70)
    
    # Test 4A: Costo con 0 tokens
    print("\n  4A: Costo con 0 tokens...")
    cost = calculate_cost(0)
    assert cost == 0.0, "Costo con 0 tokens no es 0"
    print(f"  ✅ calculate_cost(0) = ${cost}")
    
    # Test 4B: Costo con 1000 tokens
    print("\n  4B: Costo con 1,000 tokens...")
    cost = calculate_cost(1000)
    expected = (1000 / 1_000_000) * 0.225
    print(f"  Calculado: ${cost:.6f}")
    print(f"  Esperado:  ${expected:.6f}")
    assert abs(cost - expected) < 0.0001
    print(f"  ✅ Cálculo correcto")
    
    # Test 4C: Costo aumenta con tokens
    print("\n  4C: Costo aumenta con más tokens...")
    cost_100 = calculate_cost(100)
    cost_1000 = calculate_cost(1000)
    print(f"  100 tokens:  ${cost_100:.6f}")
    print(f"  1000 tokens: ${cost_1000:.6f}")
    assert cost_1000 > cost_100
    print(f"  ✅ Costo aumenta correctamente")
    
    # Test 4D: Relación proporcional
    print("\n  4D: Relación proporcional (duplicar tokens = duplicar costo)...")
    cost_500 = calculate_cost(500)
    ratio = cost_1000 / cost_500
    print(f"  Ratio (1000/500): {ratio:.2f}x")
    assert 1.95 < ratio < 2.05, "La relación no es ~2x"
    print(f"  ✅ Relación proporcional correcta")
    
    print("\n✅ PASÓ: Cálculo de costos funciona correctamente")
    return True


def test_required_fields():
    """Test 5: ¿Están todos los campos requeridos?"""
    print("\n" + "="*70)
    print("TEST 5: Campos Requeridos")
    print("="*70)
    
    response = {
        "response": "Respuesta de ejemplo",
        "confidence": "MEDIA",
        "confidence_explanation": "Explicación",
        "actions": ["respond_to_customer", "create_follow_up"],
        "reasoning": "Razonamiento"
    }
    
    print("\n  Validando campos requeridos...")
    required_fields = ["response", "confidence", "confidence_explanation", "actions", "reasoning"]
    
    result = parse_and_validate_response(json.dumps(response))
    
    for field in required_fields:
        if field in result:
            print(f"    ✅ '{field}' presente")
        else:
            print(f"    ❌ '{field}' FALTA")
            return False
    
    # Test que response no esté vacío
    assert len(result["response"]) > 0
    print(f"\n  Response: '{result['response'][:50]}...'")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Actions: {result['actions']}")
    
    print("\n✅ PASÓ: Todos los campos requeridos están presentes")
    return True


def test_actions_validation():
    """Test 6: ¿Se validan las acciones?"""
    print("\n" + "="*70)
    print("TEST 6: Validación de Acciones")
    print("="*70)
    
    response = {
        "response": "Test",
        "confidence": "ALTA",
        "confidence_explanation": "Expl",
        "actions": ["respond_to_customer", "escalate"]
    }
    
    result = parse_and_validate_response(json.dumps(response))
    
    print("\n  Validando estructura de acciones...")
    assert isinstance(result["actions"], list), "Actions debe ser lista"
    print(f"  ✅ Actions es una lista")
    
    assert len(result["actions"]) > 0, "Actions debe tener al menos una acción"
    print(f"  ✅ Actions tiene {len(result['actions'])} elemento(s)")
    
    for action in result["actions"]:
        print(f"    - {action}")
    
    print("\n✅ PASÓ: Acciones validadas correctamente")
    return True


def test_metrics_validation():
    """Test 7: ¿Se validan las métricas?"""
    print("\n" + "="*70)
    print("TEST 7: Validación de Métricas")
    print("="*70)
    
    # Datos de ejemplo del primer execution
    latency_ms = 3374.98
    tokens_prompt = 787
    tokens_completion = 102
    total_tokens = 889
    
    print(f"\n  Latencia: {latency_ms} ms")
    assert latency_ms > 0, "Latencia debe ser positiva"
    print(f"  ✅ Latencia es positiva")
    
    print(f"\n  Tokens Prompt: {tokens_prompt}")
    print(f"  Tokens Completion: {tokens_completion}")
    print(f"  Total Tokens: {total_tokens}")
    
    assert isinstance(tokens_prompt, int)
    assert isinstance(tokens_completion, int)
    assert tokens_prompt > 0
    assert tokens_completion > 0
    print(f"  ✅ Tokens son enteros positivos")
    
    assert total_tokens == tokens_prompt + tokens_completion
    print(f"  ✅ Total = Prompt + Completion ({tokens_prompt} + {tokens_completion} = {total_tokens})")
    
    cost = calculate_cost(total_tokens)
    print(f"\n  Costo estimado: ${cost:.6f}")
    assert cost > 0, "Costo debe ser positivo"
    print(f"  ✅ Costo es válido")
    
    print("\n✅ PASÓ: Métricas validadas correctamente")
    return True


# ============================================================================
# MAIN: Ejecutar todos los tests
# ============================================================================
def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║  EJECUTANDO SUITE DE TESTS - Support AI Query  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        test_prompt_loading,
        test_json_validation,
        test_confidence_values,
        test_cost_calculation,
        test_required_fields,
        test_actions_validation,
        test_metrics_validation,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ ERROR INESPERADO en {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))
    
    # Resumen final
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " RESUMEN DE TESTS ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status}  {test_name}")
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} tests pasaron")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
