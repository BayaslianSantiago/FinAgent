import sys
import uuid
from typing import Optional
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from model_factory import get_llm
from tools_finance import FINANCIAL_TOOLS, set_active_user_id
import config
import database

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SYSTEM_PROMPT = (
    "Eres 'FinAgent', un consultor experto en educación financiera, planificación presupuestaria e inversiones en Argentina.\n\n"
    "MISIÓN Y ENFOQUE:\n"
    "- Ayudar al usuario a diagnosticar su salud financiera, organizar sus gastos con la Regla 50/30/20 y hacer crecer su patrimonio.\n"
    "- Sé empático, pedagógico, motivador, claro y profesional. Usa voseo rioplatense educado y comprensible.\n"
    "- Acompaña al usuario en su realidad económica sin juzgar sus gastos.\n\n"
    "REGLA 50/30/20 (NUESTRO MARCO GUÍA):\n"
    "- 50% Necesidades Básicas (alquiler, expensas, luz, gas, comida esencial, transporte, salud).\n"
    "- 30% Gustos y Calidad de Vida (salidas, restaurantes, delivery, suscripciones streaming, ropa, hobbies).\n"
    "- 20% Ahorro e Inversión (Fondo de Emergencia, instrumentos en pesos o dólares).\n\n"
    "REGLAS OBLIGATORIAS PARA EL USO DE HERRAMIENTAS:\n"
    "1. REGISTRO DE MOVIMIENTOS: Cuando el usuario te diga que gastó, pagó, cobró o ingresó dinero (ej: 'anotá 30.000 de súper' o 'cobré 500.000 de sueldo'), llama INMEDIATAMENTE a 'registrar_gasto_o_ingreso'.\n"
    "2. CONSULTA DE BALANCE: Cuando pregunte cómo va en el mes, su saldo o su presupuesto, usa 'consultar_balance_y_presupuesto'.\n"
    "3. COTIZACIONES EN VIVO: Si pregunta el precio o cotización del dólar (Blue, MEP, Oficial, Cripto), llama a 'obtener_cotizaciones_dolar_argentina'.\n"
    "4. SIMULACIONES DE INVERSIÓN: Si pregunta cuánto ganaría en un plazo fijo o inversión, llama a 'simular_rendimiento_inversion'.\n"
    "5. METAS DE AHORRO: Si quiere ver, crear o aportar a una meta (ej: Fondo de Emergencia, vacaciones), usa 'gestionar_meta_ahorro'.\n"
    "6. CONCEPTOS E INSTRUMENTOS (RAG): Si pregunta qué es un CEDEAR, una ON, un Fondo Común (FCI), Dólar MEP o cómo armar un fondo de emergencia, consulta 'consultar_educacion_financiera_rag' para obtener definiciones oficiales precisas.\n"
    "7. SALUDOS O CHARLA GENERAL: Si el usuario solo saluda o hace una pregunta genérica sin datos numéricos, responde DIRECTAMENTE con texto cálido y ofrécele ayuda sin forzar llamadas a herramientas.\n"
    "8. AJUSTES Y CALIBRACIÓN DE INGRESOS (SUELDO): Si el usuario te indica cuánto gana en total (ej: 'gano 1.700.000', 'mi sueldo real es X'), o te pide 'bajar mis ingresos a X o en X monto' o 'subir mis ingresos', NUNCA registres un gasto para compensar. Llama INMEDIATAMENTE a 'fijar_o_ajustar_ingreso_mensual' para corregir su ingreso y recalibrar el presupuesto 50/30/20.\n"
    "9. CORREGIR O BORRAR TRANSACCIONES ERRÓNEAS: Si el usuario pide anular, eliminar o corregir un gasto o ingreso cargado por error, puedes consultar los movimientos con 'consultar_ultimos_movimientos' y luego llamar a 'eliminar_o_corregir_movimiento' con el ID correspondiente para depurar la base de datos.\n\n"
    "DESCARGO LEGAL (ÉTICA Y RESPONSABILIDAD):\n"
    "Recuerda cuando sea prudente que tus recomendaciones son de carácter educativo y orientativo; no constituyen asesoramiento financiero matriculado ante la CNV."
)

class FinancialAgent:
    def __init__(self, mode: Optional[str] = None):
        """
        Inicializa el agente financiero con el modo seleccionado ('local' o 'api').
        """
        self.mode = (mode or config.MODE).lower()
        self.llm = get_llm(self.mode)
        self.tools = FINANCIAL_TOOLS
        
        # Gestor de memoria para conversaciones multi-turno
        self.checkpointer = MemorySaver()
        self.thread_id = str(uuid.uuid4())
        
        # Creación del agente ReAct (LangGraph)
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.checkpointer
        )

    def ask(self, user_input: str, user_id: int = 1) -> str:
        """
        Envía un mensaje al agente estableciendo el ID de usuario activo
        para que las herramientas afecten a la base de datos de ese usuario.
        """
        set_active_user_id(user_id)
        run_config = {"configurable": {"thread_id": self.thread_id}}
        
        try:
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=run_config
            )
            
            messages = response.get("messages", [])
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"   [HERRAMIENTA FINANCIERA]: {tc.get('name')} con args: {tc.get('args')}")
                elif hasattr(msg, "name") and msg.name and msg.type == "tool":
                    preview = str(msg.content)[:120] + ("..." if len(str(msg.content)) > 120 else "")
                    print(f"   [RESULTADO DB/API]: {preview}")

            last_message = messages[-1] if messages else None
            if last_message:
                return str(last_message.content)
            return "No se obtuvo respuesta del modelo."

        except Exception as e:
            err_msg = str(e)
            if "does not support tools" in err_msg:
                direct_response = self.llm.invoke([
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ])
                return str(direct_response.content)
            else:
                raise e

    def clear_history(self):
        """Reinicia la memoria del hilo de conversación."""
        self.thread_id = str(uuid.uuid4())
