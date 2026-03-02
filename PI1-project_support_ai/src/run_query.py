"""
Support AI Query Executor
Integración de OpenAI API con Prompt Engineering y Métricas
Paso 4: Integración API y Estructura JSON
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================================
# PARTE 1: CONFIGURACIÓN INICIAL
# ============================================================================
# Cargamos variables de entorno desde .env
load_dotenv()

# Obtenemos la clave API de OpenAI desde variable de entorno
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError(
        "ERROR: OPENAI_API_KEY no está configurada. "
        "Crea un archivo .env con tu clave API."
    )

# Inicializamos el cliente de OpenAI
client = OpenAI(api_key=API_KEY)

# Directorio del proyecto (para cargar prompts y guardar métricas)
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
METRICS_DIR = PROJECT_ROOT / "metrics"
METRICS_FILE = METRICS_DIR / "metrics.json"

# Crear directorio de métricas si no existe
METRICS_DIR.mkdir(exist_ok=True)


# ============================================================================
# PARTE 2: CARGAR PROMPT DESDE ARCHIVO
# ============================================================================
def load_prompt(prompt_file: str = "main_prompt.txt") -> str:
    """
    Carga el prompt desde archivo.
    
    ¿Por qué lo hacemos así?
    - Separar prompt del código permite iterar sin cambiar código
    - Es más fácil de versionear y documentar
    - Los prompts son "datos", no "código"
    
    Args:
        prompt_file: Nombre del archivo en directorio prompts/
        
    Returns:
        Contenido completo del prompt
    """
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"ERROR: Prompt no encontrado en {prompt_path}. "
            f"Verifica que el archivo existe."
        )
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# PARTE 3: LLAMADA A LA API DE OPENAI
# ============================================================================
def call_openai_api(user_question: str) -> Tuple[Dict, float, int, int, int]:
    """
    Llama a OpenAI API y devuelve respuesta + métricas.
    
    ¿Qué hace?
    1. Carga el prompt con Sistema + Instrucciones + Ejemplos
    2. Envía la pregunta del usuario a gpt-4o-mini
    3. Recibe respuesta de modelo
    4. Extrae información de tokens y calcula latencia y costo
    
    ¿Por qué separamos esto en una función?
    - Responsabilidad única: solo llamar a API
    - Fácil de testear
    - Reutilizable desde otros scripts
    
    Args:
        user_question: La pregunta del usuario sobre soporte
        
    Returns:
        Tuple con (respuesta_parseada, latencia_ms, tokens_prompt, tokens_completion, total_tokens)
    """
    
    # Cargamos el prompt del archivo
    prompt_content = load_prompt()
    
    # Medimos el tiempo de inicio (para calcular latencia después)
    start_time = time.time()
    
    try:
        # Llamada a la API de OpenAI
        # Nota: Usamos gpt-4o-mini según Paso 2 (selección de modelo)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo seleccionado
            messages=[
                {
                    "role": "system",
                    "content": prompt_content  # Nuestro prompt completo
                },
                {
                    "role": "user",
                    "content": user_question  # Pregunta del usuario
                }
            ],
            temperature=0.3,      # Baja aleatoriedad (respuestas consistentes)
            max_tokens=500,       # Respuestas concisas pero completas
            top_p=0.9            # Diversidad controlada
        )
        
        # Calculamos latencia (en milisegundos)
        latency_ms = (time.time() - start_time) * 1000
        
        # Extraemos información del modelo
        response_text = response.choices[0].message.content
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        return (
            response_text,
            latency_ms,
            tokens_prompt,
            tokens_completion,
            total_tokens
        )
        
    except Exception as e:
        print(f"ERROR al llamar a OpenAI API: {e}")
        raise


# ============================================================================
# PARTE 4: PARSEAR Y VALIDAR RESPUESTA JSON
# ============================================================================
def parse_and_validate_response(response_text: str) -> Dict:
    """
    Parsea la respuesta del modelo como JSON y la valida.
    
    ¿Por qué validamos?
    - El modelo puede devolver JSON inválido a veces
    - Queremos asegurar que tiene los campos esperados
    - Esto es crítico para sistemas downstream
    
    Args:
        response_text: Respuesta cruda del modelo (debe ser JSON)
        
    Returns:
        Diccionario con respuesta validada
        
    Raises:
        ValueError: Si el JSON es inválido o faltan campos requeridos
    """
    
    try:
        # Intentamos parsear como JSON
        response_json = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"ERROR: Respuesta del modelo no es JSON válido. "
            f"Detalles: {e}\n"
            f"Respuesta recibida: {response_text[:200]}..."
        )
    
    # Validamos que tenga los campos requeridos
    required_fields = ["response", "confidence", "actions", "confidence_explanation"]
    for field in required_fields:
        if field not in response_json:
            raise ValueError(
                f"ERROR: Falta campo requerido '{field}' en respuesta JSON"
            )
    
    # Validamos que confidence sea uno de los valores permitidos
    valid_confidences = ["ALTA", "MEDIA", "BAJA"]
    if response_json["confidence"] not in valid_confidences:
        raise ValueError(
            f"ERROR: confidence debe ser ALTA/MEDIA/BAJA, "
            f"recibido: {response_json['confidence']}"
        )
    
    return response_json


# ============================================================================
# PARTE 5: CALCULAR MÉTRICAS (TOKENS, LATENCIA, COSTO)
# ============================================================================
def calculate_cost(total_tokens: int) -> float:
    """
    Calcula el costo estimado de la llamada a API.
    
    ¿Por qué es importante?
    - Los ingenieros de IA monitorean costos desde el día uno
    - API de OpenAI cobra por tokens (no por llamadas)
    - Queremos detectar si una solución es rentable
    
    Precios de gpt-4o-mini (aproximados para 2026):
    - Prompt tokens: $0.15 por 1M tokens
    - Completion tokens: $0.60 por 1M tokens
    
    Args:
        total_tokens: Número total de tokens usados
        
    Returns:
        Costo estimado en USD
    """
    
    # Precio por 1M tokens
    PRICE_PER_MILLION_TOKENS = 0.225  # Promedio (0.15 prompt + 0.60 completion)
    
    # Cálculo simple: (total_tokens / 1,000,000) * precio
    cost = (total_tokens / 1_000_000) * PRICE_PER_MILLION_TOKENS
    
    return cost


# ============================================================================
# PARTE 6: REGISTRAR MÉTRICAS EN ARCHIVO
# ============================================================================
def save_metrics(
    user_question: str,
    response: Dict,
    latency_ms: float,
    tokens_prompt: int,
    tokens_completion: int,
    total_tokens: int,
    cost_usd: float
) -> None:
    """
    Guarda métricas en un archivo JSON.
    
    ¿Por qué?
    - Auditoría: historial de todas las llamadas
    - Análisis: tendencias de costo, latencia, uso
    - Debugging: si algo falla, podemos revisar el historial
    
    Args:
        user_question: Pregunta original
        response: Respuesta del modelo (Dict)
        latency_ms: Latencia en milisegundos
        tokens_prompt: Tokens del prompt
        tokens_completion: Tokens de respuesta
        total_tokens: Total
        cost_usd: Costo en USD
    """
    
    # Crear entrada para esta ejecución
    metric_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_question": user_question,
        "confidence_returned": response.get("confidence"),
        "latency_ms": round(latency_ms, 2),
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(cost_usd, 6),
    }
    
    # Leer métricas existentes (si existen)
    metrics_list = []
    if METRICS_FILE.exists():
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            try:
                metrics_list = json.load(f)
            except json.JSONDecodeError:
                metrics_list = []
    
    # Agregar nueva métrica
    metrics_list.append(metric_entry)
    
    # Guardar actualizado
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics_list, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Métricas guardadas en {METRICS_FILE}")


# ============================================================================
# PARTE 7: FUNCIÓN PRINCIPAL - ORQUESTAR TODO
# ============================================================================
def run_support_query(user_question: str) -> Dict:
    """
    Función principal que orquesta todo el proceso.
    
    Flujo:
    1. Recibe pregunta del usuario
    2. Llama a OpenAI (con prompt cargado)
    3. Parsea respuesta JSON
    4. Calcula métricas
    5. Guarda en archivo
    6. Retorna respuesta estructurada
    
    Args:
        user_question: La pregunta del usuario
        
    Returns:
        Dict con respuesta del modelo + métricas
    """
    
    print(f"\n🔄 Procesando pregunta: {user_question[:80]}...")
    
    # Paso 1: Llamar a OpenAI
    try:
        response_text, latency_ms, tokens_prompt, tokens_completion, total_tokens = call_openai_api(
            user_question
        )
    except Exception as e:
        print(f"❌ Error al llamar API: {e}")
        return {"error": str(e)}
    
    # Paso 2: Parsear respuesta
    try:
        response_json = parse_and_validate_response(response_text)
    except ValueError as e:
        print(f"❌ Error validando respuesta: {e}")
        return {"error": str(e)}
    
    # Paso 3: Calcular costo
    cost_usd = calculate_cost(total_tokens)
    
    # Paso 4: Guardar métricas
    save_metrics(
        user_question=user_question,
        response=response_json,
        latency_ms=latency_ms,
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
        total_tokens=total_tokens,
        cost_usd=cost_usd
    )
    
    # Paso 5: Construir respuesta completa con métricas
    result = {
        **response_json,  # Incluir respuesta original
        "metrics": {
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "estimated_cost_usd": round(cost_usd, 6)
        }
    }
    
    return result


# ============================================================================
# PARTE 8: ENTRADA DEL SCRIPT (SI SE EJECUTA DIRECTAMENTE)
# ============================================================================
if __name__ == "__main__":
    # Si no se proporciona pregunta en línea de comandos, usamos una de ejemplo
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Mi contraseña no funciona, ¿qué puedo hacer?"
    
    # Ejecutar
    result = run_support_query(question)
    
    # Mostrar resultado formateado
    print("\n" + "="*70)
    print("📋 RESULTADO FINAL")
    print("="*70)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*70)
