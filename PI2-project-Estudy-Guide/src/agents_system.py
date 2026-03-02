"""
AGENTS SYSTEM - Level 3 
Implementa function calling para que el LLM ejecute acciones automáticas
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from openai import OpenAI

client = OpenAI()


class AgentTools:
    """Define las herramientas (tools) disponibles para el agent"""
    
    @staticmethod
    def get_tools_definitions() -> List[Dict]:
        """Retorna las definiciones de herramientas para OpenAI"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_support_ticket",
                    "description": "Crea un nuevo ticket de soporte en el sistema",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue": {
                                "type": "string",
                                "description": "Descripción clara del problema del cliente"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Nivel de prioridad del ticket"
                            },
                            "customer_email": {
                                "type": "string",
                                "description": "Email del cliente para contacto"
                            }
                        },
                        "required": ["issue", "priority", "customer_email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_specialist",
                    "description": "Escala el problema a un especialista",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Razón de la escalación"
                            },
                            "team": {
                                "type": "string",
                                "enum": ["technical", "billing", "legal"],
                                "description": "Equipo especialista"
                            }
                        },
                        "required": ["reason", "team"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_callback",
                    "description": "Agenda una llamada con el cliente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_phone": {
                                "type": "string",
                                "description": "Número de teléfono del cliente"
                            },
                            "preferred_time": {
                                "type": "string",
                                "description": "Hora preferida en formato HH:MM"
                            },
                            "timezone": {
                                "type": "string",
                                "enum": ["UTC", "EST", "PST", "CST"],
                                "description": "Zona horaria"
                            }
                        },
                        "required": ["customer_phone", "preferred_time", "timezone"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_notification_email",
                    "description": "Envía un email de notificación al cliente",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email del cliente"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Asunto del email"
                            },
                            "body": {
                                "type": "string",
                                "description": "Contenido del email"
                            }
                        },
                        "required": ["email", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_refund",
                    "description": "Aprueba un reembolso automático",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "ID único del cliente"
                            },
                            "refund_amount": {
                                "type": "number",
                                "description": "Monto del reembolso en USD"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Razón del reembolso"
                            }
                        },
                        "required": ["customer_id", "refund_amount", "reason"]
                    }
                }
            }
        ]


class ActionExecutor:
    """Ejecuta las acciones determinadas por el LLM"""
    
    def __init__(self, actions_log_dir: str = "actions_log"):
        self.actions_log_dir = actions_log_dir
        os.makedirs(actions_log_dir, exist_ok=True)
    
    def execute_action(self, action_name: str, params: Dict) -> Dict[str, Any]:
        """Ejecuta una acción específica"""
        
        result = {
            "action": action_name,
            "timestamp": datetime.now().isoformat(),
            "params": params,
            "status": "success"
        }
        
        try:
            if action_name == "create_support_ticket":
                return self._create_ticket(params, result)
            elif action_name == "escalate_to_specialist":
                return self._escalate(params, result)
            elif action_name == "schedule_callback":
                return self._schedule_callback(params, result)
            elif action_name == "send_notification_email":
                return self._send_email(params, result)
            elif action_name == "approve_refund":
                return self._approve_refund(params, result)
            else:
                result["status"] = "error"
                result["error"] = f"Acción desconocida: {action_name}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _create_ticket(self, params: Dict, result: Dict) -> Dict:
        """Crea un ticket de soporte"""
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result["ticket_id"] = ticket_id
        result["message"] = f"Ticket {ticket_id} creado con prioridad {params['priority']}"
        result["customer_email"] = params["customer_email"]
        
        # Log the action
        self._log_action(result)
        
        return result
    
    def _escalate(self, params: Dict, result: Dict) -> Dict:
        """Escala a especialista"""
        escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result["escalation_id"] = escalation_id
        result["team"] = params["team"]
        result["message"] = f"Escalado a equipo {params['team']}: {params['reason']}"
        
        self._log_action(result)
        
        return result
    
    def _schedule_callback(self, params: Dict, result: Dict) -> Dict:
        """Agenda una llamada"""
        callback_id = f"CB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result["callback_id"] = callback_id
        result["phone"] = params["customer_phone"]
        result["time"] = params["preferred_time"]
        result["message"] = f"Llamada agendada para {params['preferred_time']} {params['timezone']}"
        
        self._log_action(result)
        
        return result
    
    def _send_email(self, params: Dict, result: Dict) -> Dict:
        """Envía un email"""
        email_id = f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result["email_id"] = email_id
        result["recipient"] = params["email"]
        result["message"] = f"Email enviado a {params['email']}"
        
        self._log_action(result)
        
        return result
    
    def _approve_refund(self, params: Dict, result: Dict) -> Dict:
        """Aprueba un reembolso"""
        refund_id = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result["refund_id"] = refund_id
        result["amount"] = params["refund_amount"]
        result["message"] = f"Reembolso {refund_id} de ${params['refund_amount']} aprobado"
        
        self._log_action(result)
        
        return result
    
    def _log_action(self, result: Dict):
        """Registra la acción en archivo JSON"""
        log_file = os.path.join(self.actions_log_dir, "actions.json")
        
        actions = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                actions = json.load(f)
        
        actions.append(result)
        
        with open(log_file, 'w') as f:
            json.dump(actions, f, indent=2)


class AgentOrchestrator:
    """Orquesta todo el flujo de Agent con function calling"""
    
    def __init__(self, system_prompt: str, rag_system=None):
        self.system_prompt = system_prompt
        self.rag_system = rag_system
        self.action_executor = ActionExecutor()
        self.tools = AgentTools.get_tools_definitions()
    
    def process_query(self, user_question: str, customer_email: str = "unknown@company.com") -> Dict:
        """Procesa una consulta con agent + function calling"""
        
        # Build the message with RAG context if available
        if self.rag_system:
            user_message = self.rag_system.get_rag_prompt(user_question, self.system_prompt)
        else:
            user_message = f"{self.system_prompt}\n\nPregunta: {user_question}"
        
        # First call to LLM with tools
        messages = [{"role": "user", "content": user_message}]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        # Process response
        result = {
            "user_question": user_question,
            "customer_email": customer_email,
            "response": "",
            "confidence": "MEDIA",
            "actions_executed": [],
            "metrics": {}
        }
        
        # Extract message and tool calls
        response_message = response.choices[0].message
        
        if response_message.content:
            result["response"] = response_message.content[:300]
        
        # Execute any tool calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                action_result = self.action_executor.execute_action(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                result["actions_executed"].append(action_result)
        
        # Extract metrics
        result["metrics"] = {
            "tokens_prompt": response.usage.prompt_tokens,
            "tokens_completion": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "estimated_cost_usd": (response.usage.total_tokens / 1_000_000) * 0.225,
            "tools_used": len(response_message.tool_calls) if response_message.tool_calls else 0
        }
        
        return result
