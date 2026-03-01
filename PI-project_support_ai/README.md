# Support AI Query - README

Aplicación de Consulta de Soporte Técnico impulsada por IA con Prompt Engineering y Métricas.

## 🎯 Objetivo

Procesar preguntas de soporte técnico y devolver respuestas estructuradas en JSON con:
- Respuesta generada por IA
- Estimación de confianza
- Acciones recomendadas
- Métricas de rendimiento (tokens, latencia, costo)

## 🚀 Quick Start

### 1. Requisitos Previos
- Python 3.10+
- Clave API de OpenAI (obtén la tuya en https://platform.openai.com/api-keys)

### 2. Instalación

```bash
# Clonar o descargar proyecto
cd 06_project_support_ai

# Instalar dependencias
pip install openai python-dotenv

# Crear archivo .env (basado en .env.example)
cp .env.example .env

# IMPORTANTE: Editar .env y agregar tu clave API
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Ejecutar

```bash
# Ejecutar con pregunta por defecto
python src/run_query.py

# Ejecutar con pregunta personalizada
python src/run_query.py "Mi contraseña no funciona"

# Ver métricas guardadas
cat metrics/metrics.json
```

### 4. Ejecutar Tests

```bash
# Tests automatizados (sin dependencia de pytest)
python tests/simple_tests.py

# (Opcional) Tests con pytest
pip install pytest
pytest tests/test_core.py -v
```

## 📁 Estructura del Proyecto

```
06_project_support_ai/
├── src/run_query.py                 ← Script principal
├── prompts/main_prompt.txt          ← Prompt Few-Shot
├── metrics/metrics.json             ← Histórico de métricas
├── tests/
│   ├── simple_tests.py              ← Tests independientes
│   └── test_core.py                 ← Tests con pytest
├── docs/
│   ├── problem_definition.md        ← Definición de tarea
│   └── PI_report_en.md              ← Reporte técnico completo
├── .env.example                     ← Template de variables
├── .env                             ← Tu clave API (NO en Git)
├── .gitignore                       ← Excluye archivos sensibles
├── pyproject.toml                   ← Dependencias
└── README.md                        ← Este archivo
```

## 🔧 Cómo Funciona

### Flujo de Ejecución

1. **Entrada:** Usuario escribe pregunta de soporte
2. **Carga Prompt:** Lee `prompts/main_prompt.txt`
3. **Llamada API:** Envía a OpenAI (gpt-4o-mini)
4. **Validación:** Verifica JSON y campos requeridos
5. **Métricas:** Calcula tokens, latencia, costo
6. **Registro:** Guarda en `metrics/metrics.json`
7. **Salida:** Retorna respuesta estructurada en JSON

### Arquitectura del Código

**`src/run_query.py`** (8 partes):
1. Configuración (carga API key)
2. Carga Prompt desde archivo
3. Llamada a OpenAI API
4. Validación de JSON
5. Cálculo de costos
6. Registro de métricas
7. Orquestación (une todo)
8. Entrada/Salida

**`prompts/main_prompt.txt`**:
- System Prompt: Define rol
- Instructions: Criterios de confianza
- Format: JSON schema
- Examples: 3 ejemplos Few-Shot

## 📊 Ejemplo de Salida

**Entrada:**
```
"Mi contraseña no funciona, ¿qué puedo hacer?"
```

**Salida:**
```json
{
  "response": "Haz clic en 'Olvidé mi contraseña' en la pantalla de inicio de sesión. Recibirás un correo para restablecerla. Si no llega, revisa la carpeta de spam.",
  "confidence": "ALTA",
  "confidence_explanation": "Es un procedimiento estándar y bien documentado.",
  "actions": ["respond_to_customer"],
  "reasoning": "Solución directa y probada para problema común.",
  "metrics": {
    "tokens_prompt": 787,
    "tokens_completion": 102,
    "total_tokens": 889,
    "latency_ms": 3374.98,
    "estimated_cost_usd": 0.0002
  }
}
```

## 🧪 Tests

### Ejecutar Tests

```bash
# Tests simples (no necesita pytest)
python tests/simple_tests.py

# Output esperado: 7/7 tests PASARON
```

### Qué se Valida

| Test | Descripción |
|------|-------------|
| Prompt Loading | Archivo existe y tiene contenido |
| JSON Validation | Respuesta es JSON válido |
| Confidence Values | Solo ALTA/MEDIA/BAJA |
| Cost Calculation | Fórmula correcta ($0.225 por 1M tokens) |
| Required Fields | Todos los campos presentes |
| Actions Validation | Lista no vacía |
| Metrics Validation | Valores positivos y consistentes |

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Importante:**
- Nunca compartas tu `.env`
- Está en `.gitignore` para no subir a Git
- Cada desarrollador debe tener su propia clave

### Modelo y Parámetros

En `src/run_query.py`:
```python
client.chat.completions.create(
    model="gpt-4o-mini",      # Modelo seleccionado (bajo costo)
    temperature=0.3,           # Baja aleatoriedad
    max_tokens=500,            # Respuestas concisas
    top_p=0.9                  # Diversidad controlada
)
```

## 📈 Monitoreo de Métricas

### Archivo de Métricas

Cada ejecución se registra en `metrics/metrics.json`:

```json
[
  {
    "timestamp": "2026-03-01T19:24:23.975226",
    "user_question": "Mi contraseña no funciona...",
    "confidence_returned": "ALTA",
    "latency_ms": 3374.98,
    "tokens_prompt": 787,
    "tokens_completion": 102,
    "total_tokens": 889,
    "estimated_cost_usd": 0.0002
  }
]
```

### Análisis de Métricas

```python
import json

# Leer métricas
with open("metrics/metrics.json") as f:
    metrics = json.load(f)

# Calcular promedio de latencia
avg_latency = sum(m["latency_ms"] for m in metrics) / len(metrics)
print(f"Latencia promedio: {avg_latency:.0f} ms")

# Costo total
total_cost = sum(m["estimated_cost_usd"] for m in metrics)
print(f"Costo total: ${total_cost:.4f}")

# Confianza promedio
confidences = [m["confidence_returned"] for m in metrics]
print(f"Confianzas: {confidences}")
```

## 🔒 Seguridad

### Mejores Prácticas

✅ **Clave API en .env, no en código**
```python
# BIEN: Leer de .env
API_KEY = os.getenv("OPENAI_API_KEY")

# MAL: Hardcodear clave
API_KEY = "sk-abc123"  # ❌ NUNCA HAGAS ESTO
```

✅ **Validación de entrada y salida**
```python
# Valida JSON
if not isinstance(response_json, dict):
    raise ValueError("Invalid response")

# Valida campos
if "confidence" not in response_json:
    raise ValueError("Missing confidence field")
```

✅ **Monitoreo de costos**
- Registra costo por llamada
- Suma periódicamente para detectar anomalías
- Alert si costo > presupuesto

### Riesgos Conocidos

| Riesgo | Mitigación |
|--------|-----------|
| Alucinación del modelo | Validación humana para confidence BAJA |
| JSON inválido | Fallback a template predefinido |
| Costos altos | Usar gpt-4o-mini, monitorear |
| Prompts adversariales | Entrada validada, límites de tamaño |

## 🚀 Próximos Pasos

### Fase 2: Producción
- [ ] Implementar RAG (Retrieval-Augmented Generation)
- [ ] Conectar base de conocimiento interna
- [ ] Dashboard de métricas en tiempo real

### Fase 3: Escalamiento
- [ ] API REST wrapper
- [ ] Rate limiting
- [ ] Logging a base de datos

### Fase 4: Optimización
- [ ] A/B testing: gpt-4o-mini vs gpt-4o
- [ ] Fine-tuning en datos propios
- [ ] Cache de prompts frecuentes

## 📖 Documentación

- **Paso 1:** [problem_definition.md](docs/problem_definition.md) - Definición de tarea
- **Paso 5:** [PI_report_en.md](docs/PI_report_en.md) - Reporte técnico

## 🤝 Soporte

Si encuentras problemas:

1. Verifica que tienes clave API válida
2. Ejecuta tests: `python tests/simple_tests.py`
3. Revisa el archivo de error en logs
4. Consulta el reporte técnico en `docs/PI_report_en.md`

## 📝 Licencia

Este proyecto es parte del curso de AI Engineering de Henry.

---

**Versión:** 1.0
**Última actualización:** Marzo 1, 2026
