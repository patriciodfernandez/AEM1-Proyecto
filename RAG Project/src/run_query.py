"""
Support AI Query - CON RAG (Nivel 2) + AGENTS (Nivel 3)
Integración de OpenAI API + Prompt Engineering + RAG + Agents + Métricas
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List, Any

from dotenv import load_dotenv
from openai import OpenAI

# Importar RAG System (Nivel 2)
from rag_system import RAGSystem

# Importar Agents System (Nivel 3)
from agents_system import AgentTools, get_openai_tools_definition, execute_tool_call


# ============================================================================
# PARTE 1: CONFIGURACIÓN INICIAL
# ============================================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError(
        "ERROR: OPENAI_API_KEY no está configurada. "
        "Crea un archivo .env con tu clave API."
    )

client = OpenAI(api_key=API_KEY)

PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
METRICS_DIR = PROJECT_ROOT / "metrics"
METRICS_FILE = METRICS_DIR / "metrics.json"

METRICS_DIR.mkdir(exist_ok=True)

# Inicializar RAG System
print("\n⏳ Inicializando sistema (primer acceso puede tomar 1-2 min)...")
rag_system = RAGSystem(API_KEY)

# Inicializar Agents System (Nivel 3)
agent_tools = AgentTools()


# ============================================================================
# PARTE 2: CARGAR PROMPT BASE
# ============================================================================

def load_prompt(prompt_file: str = "main_prompt.txt") -> str:
    """Carga el prompt base desde archivo"""
    
    prompt_path = PROMPTS_DIR / prompt_file
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt no encontrado en {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# PARTE 3: LLAMADA A OPENAI CON RAG + AGENTS
# ============================================================================

def call_openai_api(user_question: str) -> Tuple[Dict, float, int, int, int, List[Dict]]:
    """
    Llama a OpenAI API con contexto RAG + Agents (Nivel 3)
    
    ¿Qué hace?
    1. Carga prompt base
    2. Recupera contexto de knowledge_base (RAG)
    3. Agrega contexto al prompt
    4. Envía a OpenAI CON TOOLS (Agents)
    5. Si LLM usa tools, las ejecuta
    6. Retorna respuesta + métricas + acciones ejecutadas
    """
    
    prompt_content = load_prompt()
    
    # Recuperar contexto usando RAG
    context = rag_system.retrieve_context(user_question, k=3)
    
    # Agregar contexto al prompt
    if context:
        prompt_content += f"\n\n{context}"
        prompt_content += "\n\nResponde basado en este contexto de la base de conocimiento. Si la información no está disponible, indícalo claramente."
    
    start_time = time.time()
    executed_actions = []
    
    try:
        # PRIMER LLAMADA: Con tools disponibles
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt_content
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            tools=get_openai_tools_definition(),  # NUEVO: Agregamos tools
            temperature=0.3,
            max_tokens=500,
            top_p=0.9
        )
        
        # Verificar si el LLM quiere usar tools
        assistant_message = response.choices[0].message
        
        # Si hay tool_calls, ejecutarlos
        if assistant_message.tool_calls:
            messages = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": user_question},
                {"role": "assistant", "content": assistant_message.content or "", "tool_calls": assistant_message.tool_calls}
            ]
            
            # Ejecutar cada tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                
                # Ejecutar la herramienta
                tool_result = execute_tool_call(tool_name, tool_input, agent_tools)
                executed_actions.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": tool_result
                })
                
                # Agregar resultado al mensaje
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            # SEGUNDA LLAMADA: Enviar resultados de tools
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=500,
                top_p=0.9
            )
            
            response_text = final_response.choices[0].message.content
            tokens_prompt = final_response.usage.prompt_tokens
            tokens_completion = final_response.usage.completion_tokens
            total_tokens = final_response.usage.total_tokens
        else:
            # Sin tool calls, solo respuesta
            response_text = assistant_message.content
            tokens_prompt = response.usage.prompt_tokens
            tokens_completion = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
        
        latency_ms = (time.time() - start_time) * 1000
        
        return (
            response_text,
            latency_ms,
            tokens_prompt,
            tokens_completion,
            total_tokens,
            executed_actions  # NUEVO: Retorna acciones ejecutadas
        )
        
    except Exception as e:
        print(f"ERROR al llamar a OpenAI API: {e}")
        raise


# ============================================================================
# PARTE 4: VALIDAR RESPUESTA JSON
# ============================================================================

def parse_and_validate_response(response_text: str) -> Dict:
    """Parsea y valida respuesta JSON"""
    
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"ERROR: Respuesta no es JSON válido: {e}")
    
    required_fields = ["response", "confidence", "actions", "confidence_explanation"]
    for field in required_fields:
        if field not in response_json:
            raise ValueError(f"ERROR: Falta campo requerido '{field}'")
    
    valid_confidences = ["ALTA", "MEDIA", "BAJA"]
    if response_json["confidence"] not in valid_confidences:
        raise ValueError(
            f"ERROR: confidence debe ser ALTA/MEDIA/BAJA, "
            f"recibido: {response_json['confidence']}"
        )
    
    return response_json


# ============================================================================
# PARTE 5: CALCULAR COSTO
# ============================================================================

def calculate_cost(total_tokens: int) -> float:
    """Calcula costo estimado"""
    
    PRICE_PER_MILLION_TOKENS = 0.225
    return (total_tokens / 1_000_000) * PRICE_PER_MILLION_TOKENS


# ============================================================================
# PARTE 6: GUARDAR MÉTRICAS
# ============================================================================

def save_metrics(
    user_question: str,
    response: Dict,
    latency_ms: float,
    tokens_prompt: int,
    tokens_completion: int,
    total_tokens: int,
    cost_usd: float,
    rag_context_used: bool = True,
    executed_actions: List[Dict] = None  # NUEVO: Acciones ejecutadas por agents
) -> None:
    """Guarda métricas con información RAG + Agents"""
    
    if executed_actions is None:
        executed_actions = []
    
    metric_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_question": user_question,
        "confidence_returned": response.get("confidence"),
        "latency_ms": round(latency_ms, 2),
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(cost_usd, 6),
        "rag_enabled": rag_context_used,
        "agents_actions_executed": len(executed_actions) > 0,  # NUEVO
        "actions_details": executed_actions if executed_actions else None  # NUEVO
    }
    
    metrics_list = []
    if METRICS_FILE.exists():
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            try:
                metrics_list = json.load(f)
            except json.JSONDecodeError:
                metrics_list = []
    
    metrics_list.append(metric_entry)
    
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics_list, f, indent=2, ensure_ascii=False)
    
    action_count = len(executed_actions)
    if action_count > 0:
        print(f"✓ Métricas guardadas (RAG: {'activado' if rag_context_used else 'desactivado'}, Agents: {action_count} acciones)")


# ============================================================================
# PARTE 7: FUNCIÓN PRINCIPAL
# ============================================================================

def run_support_query(user_question: str, use_rag: bool = True, use_agents: bool = True) -> Dict:
    """
    Ejecuta consulta de soporte con opción de RAG + Agents
    
    Args:
        user_question: Pregunta del usuario
        use_rag: Usar RAG o solo LLM (para comparar)
        use_agents: Usar Agents para acciones (Level 3)
    
    Returns:
        Dict con respuesta, confianza, acciones y métricas
    """
    
    print(f"\n🔄 Procesando pregunta: {user_question[:80]}...")
    features = []
    if use_rag:
        print("   (Con RAG activado)")
        features.append("RAG")
    if use_agents:
        print("   (Con Agents activado)")
        features.append("Agents")
    
    try:
        # Llamar a OpenAI NIVEL 3 (con RAG + Agents)
        response_text, latency_ms, tokens_prompt, tokens_completion, total_tokens, executed_actions = call_openai_api(
            user_question
        )
    except Exception as e:
        print(f"❌ Error al llamar API: {e}")
        return {"error": str(e)}
    
    # Validar respuesta
    try:
        response_json = parse_and_validate_response(response_text)
    except ValueError as e:
        print(f"❌ Error validando respuesta: {e}")
        return {"error": str(e)}
    
    # Calcular costo
    cost_usd = calculate_cost(total_tokens)
    
    # Guardar métricas
    save_metrics(
        user_question=user_question,
        response=response_json,
        latency_ms=latency_ms,
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        rag_context_used=use_rag,
        executed_actions=executed_actions if use_agents else []
    )
    
    # Construir resultado final
    result = {
        **response_json,
        "metrics": {
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "estimated_cost_usd": round(cost_usd, 6),
            "rag_enabled": use_rag,
            "agents_enabled": use_agents,
            "actions_executed": executed_actions if executed_actions else None
        }
    }
    
    return result


# ============================================================================
# PARTE 8: ENTRADA DEL SCRIPT
# ============================================================================

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "¿Cuál es la política de reembolso?"
    
    # Ejecutar Nivel 3: RAG + Agents
    result = run_support_query(question, use_rag=True, use_agents=True)
    
    print("\n" + "="*70)
    print("📋 RESULTADO FINAL (NIVEL 3: RAG + AGENTS)")
    print("="*70)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*70)
