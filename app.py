import os
import chainlit as cl
from chainlit.input_widget import Select
from typing import Optional

from chainlit.server import app as fastapi_app
from fastapi.responses import JSONResponse

import config
import database
import dashboard_charts
from agent import FinancialAgent

# Inicializar la base de datos SQLite y usuario demo al arrancar el servidor
database.init_db()

# ==============================================================================
# ENDPOINT DE DATOS EN TIEMPO REAL PARA EL DASHBOARD PATRIMONIAL
# ==============================================================================

@fastapi_app.get("/api/dashboard-data")
def api_dashboard_data(user_id: int = 1):
    """Provee los datos consolidados en JSON para la vista del Dashboard Ejecutivo."""
    summary = database.get_monthly_summary(user_id)
    txs = database.get_recent_transactions(user_id, limit=50)
    goals = database.get_goals(user_id)
    user_info = database.get_user_by_id(user_id)
    return JSONResponse({
        "summary": summary,
        "transactions": txs,
        "goals": goals,
        "user": user_info or {"nombre_completo": "Martín Gómez", "perfil_inversor": "Moderado"}
    })


# ==============================================================================
# AUTENTICACIÓN SEGURA DE USUARIOS (Chainlit Auth Callback)
# ==============================================================================

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Verifica las credenciales del usuario contra la base de datos SQLite.
    Las contraseñas se validan con PBKDF2/SHA-256 (hashing seguro).
    Usuario demo por defecto: demo / demo123
    """
    user_data = database.authenticate_user(username, password)
    if user_data:
        return cl.User(
            identifier=user_data["username"],
            metadata={
                "id": user_data["id"],
                "nombre": user_data["nombre_completo"],
                "perfil": user_data["perfil_inversor"]
            }
        )
    return None

# ==============================================================================
# CONFIGURACIÓN Y SELECTOR DE MOTOR (Groq API vs Ollama Local)
# ==============================================================================

@cl.set_starters
async def set_starters():
    """Botones de inicio rápido con la estética institucional de FinAgent."""
    return [
        cl.Starter(
            label="Dashboard y Gráficos",
            message="Mostrame mi dashboard financiero con los gráficos de gastos y balance",
            icon="/public/starters/chart.svg",
        ),
        cl.Starter(
            label="💵 Cotizaciones Dólar en Vivo",
            message="¿A cuánto cotiza el dólar hoy en Argentina (Oficial, Blue, MEP, Cripto y Tarjeta)?",
            icon="/public/starters/dolar.svg",
        ),
        cl.Starter(
            label="📊 Diagnóstico Presupuesto 50/30/20",
            message="Consultar mi balance mensual y análisis de gastos bajo la regla 50/30/20",
            icon="/public/starters/balance.svg",
        ),
        cl.Starter(
            label="📈 Simular Plazo Fijo / Fondos",
            message="Simular rendimiento de una inversión de $500.000 a 30 días",
            icon="/public/starters/chart.svg",
        ),
        cl.Starter(
            label="📚 Base RAG: ¿Qué es un CEDEAR?",
            message="Explicame qué es un CEDEAR, qué ventajas tiene y qué riesgo conlleva en Argentina",
            icon="/public/starters/book.svg",
        ),
    ]

@cl.on_chat_start
async def on_chat_start():
    """
    Se ejecuta cuando el usuario inicia sesión.
    Prepara la instancia personal del agente y le da la bienvenida con sus datos.
    """
    # 1. Selector de modo (Groq API vs Ollama Local) en los ajustes de Chainlit
    default_mode = config.MODE
    await cl.ChatSettings([
        Select(
            id="agent_mode",
            label="Motor de IA (Modo)",
            values=["api", "local"],
            initial_value=default_mode,
            description="API (Groq): Ultra rápido con modelos de 120B | Local (Ollama): 100% offline y privado."
        )
    ]).send()

    # 2. Obtener datos del usuario autenticado
    user: cl.User = cl.user_session.get("user")
    user_id = user.metadata.get("id", 1) if user else 1
    nombre = user.metadata.get("nombre", "Usuario") if user else "Usuario"
    perfil = user.metadata.get("perfil", "Moderado") if user else "Moderado"

    # 3. Instanciar el agente financiero para esta sesión
    agent = FinancialAgent(mode=default_mode)
    cl.user_session.set("agent", agent)
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("current_mode", default_mode)

    # 4. Consultar estado financiero actual del usuario en la base de datos
    summary = database.get_monthly_summary(user_id)
    saldo = summary.get("saldo_disponible", 0.0)
    ingresos = summary.get("total_ingresos", 0.0)
    gastos = summary.get("total_gastos", 0.0)
    mes = summary.get("mes_año", "")

    modo_actual = "Groq Cloud API (⚡ Ultra Rápido)" if default_mode == "api" else "Ollama Local (🏠 Offline)"

    # Mensaje de bienvenida enriquecido con componentes visuales de alta gama
    welcome_text = (
        f'<div class="fin-card gold-accent">\n'
        f'  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">\n'
        f'    <span class="fin-badge gold">§ Sesión Autenticada</span>\n'
        f'    <span class="fin-badge emerald">{modo_actual}</span>\n'
        f'  </div>\n'
        f'  <h3 style="margin:4px 0 6px 0; color:#FFFFFF; font-family:\'Playfair Display\', serif; font-size:1.35rem;">¡Bienvenido, {nombre}!</h3>\n'
        f'  <p style="margin:0; font-size:0.88rem; color:#94A3B8;">Panel Patrimonial Inteligente · <em>Perfil Inversor: <strong style="color:#D4AF37;">{perfil}</strong></em></p>\n'
        f'</div>\n\n'
        f'<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 12px 0;">\n'
        f'  <div class="fin-card" style="margin:0; padding:14px 16px;">\n'
        f'    <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em;">Ingresos ({mes})</div>\n'
        f'    <div style="font-size:1.25rem; font-weight:700; color:#10B981; font-family:\'JetBrains Mono\', monospace; margin-top:4px;">${ingresos:,.2f}</div>\n'
        f'  </div>\n'
        f'  <div class="fin-card" style="margin:0; padding:14px 16px;">\n'
        f'    <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em;">Gastos ({mes})</div>\n'
        f'    <div style="font-size:1.25rem; font-weight:700; color:#F59E0B; font-family:\'JetBrains Mono\', monospace; margin-top:4px;">${gastos:,.2f}</div>\n'
        f'  </div>\n'
        f'  <div class="fin-card" style="margin:0; padding:14px 16px;">\n'
        f'    <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em;">Saldo Disponible</div>\n'
        f'    <div style="font-size:1.25rem; font-weight:700; color:#D4AF37; font-family:\'JetBrains Mono\', monospace; margin-top:4px;">${saldo:,.2f}</div>\n'
        f'  </div>\n'
        f'</div>\n\n'
        f'💡 **¿Qué te gustaría gestionar hoy?**\n'
        f'• Podés hacer clic en cualquiera de los **accesos directos** de abajo.\n'
        f'• Abrir el **[Dashboard](/public/dashboard.html)** en una pestaña dedicada.\n'
        f'• Registrar transacciones por voz o texto (*"Anotá 32.000 de compras de supermercado"*).\n\n'
        f'> ⚖️ *Aviso ético: FinAgent proporciona educación financiera y asistencia de presupuesto personal; no constituye asesoramiento financiero matriculado CNV.*'
    )

    await cl.Message(content=welcome_text).send()

@cl.on_settings_update
async def on_settings_update(settings):
    """Permite cambiar de modo (Groq vs Ollama) en caliente desde la interfaz web."""
    new_mode = settings.get("agent_mode", "api")
    cl.user_session.set("agent", FinancialAgent(mode=new_mode))
    cl.user_session.set("current_mode", new_mode)
    
    desc = "Groq API (Ultra Rápido ⚡)" if new_mode == "api" else "Ollama Local (Offline 🏠)"
    await cl.Message(content=f"🔄 **Motor cambiado a:** `{desc}`").send()

# ==============================================================================
# PROCESAMIENTO DE MENSAJES Y RENDERIZADO VISUAL
# ==============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    """
    Recibe los mensajes del usuario, detecta solicitudes de dashboard gráfico
    o delega en el agente financiero ReAct.
    """
    user_input = message.content.strip()

    # Comando rápido para alternar modo por chat
    if user_input.lower().startswith("/mode"):
        parts = user_input.split()
        if len(parts) == 2 and parts[1].lower() in ["api", "local"]:
            new_mode = parts[1].lower()
            cl.user_session.set("agent", FinancialAgent(mode=new_mode))
            cl.user_session.set("current_mode", new_mode)
            desc = "Groq API (Ultra Rápido ⚡)" if new_mode == "api" else "Ollama Local (Offline 🏠)"
            await cl.Message(content=f"🔄 **Motor cambiado a:** `{desc}`").send()
            return
        else:
            await cl.Message(content="Uso del comando: `/mode api` o `/mode local`").send()
            return

    agent: FinancialAgent = cl.user_session.get("agent")
    user_id = cl.user_session.get("user_id", 1)
    current_mode = cl.user_session.get("current_mode", config.MODE)

    if not agent:
        agent = FinancialAgent(mode=current_mode)
        cl.user_session.set("agent", agent)

    # 1. Detección Inteligente de Solicitud de Dashboard / Gráficos en el Chat
    query_lower = user_input.lower()
    is_dashboard_req = any(w in query_lower for w in [
        "dashboard", "gráfico", "grafico", "gráficos", "graficos", "ver balance", "ver métricas", "ver metricas"
    ])

    if is_dashboard_req:
        async with cl.Step(name="Generando gráficos interactivos de tu patrimonio..."):
            summary = database.get_monthly_summary(user_id)
            txs = database.get_recent_transactions(user_id, limit=8)

            fig_donut = dashboard_charts.generate_503020_donut_chart(summary)
            fig_bar = dashboard_charts.generate_category_bar_chart(user_id)

            elements = [
                cl.Plotly(name="chart_503020", figure=fig_donut, display="inline"),
                cl.Plotly(name="chart_categories", figure=fig_bar, display="inline")
            ]

            # Construir tabla rápida de movimientos
            tx_table = [
                "| ID | Fecha | Tipo | Categoría | Detalle | Importe |",
                "| :--- | :--- | :--- | :--- | :--- | :---: |"
            ]
            for t in txs:
                badge = "🟢 Ingreso" if t["tipo"] == "ingreso" else "🔴 Gasto"
                tx_table.append(f"| `#{t['id']}` | {t['fecha']} | {badge} | **{t['categoria']}** | {t['descripcion'] or '—'} | `${t['monto']:,.2f}` |")

            table_str = "\n".join(tx_table)

            reply = (
                f"### Dashboard del Período ({summary['mes_año']})\n\n"
                f"• **Ingresos Totales:** `${summary['total_ingresos']:,.2f}`\n"
                f"• **Gastos Totales:** `${summary['total_gastos']:,.2f}`\n"
                f"• **Saldo Disponible:** `${summary['saldo_disponible']:,.2f}`\n\n"
                f"#### 📝 Últimos Movimientos Registrados:\n{table_str}\n\n"
                f"> 💡 *Podés acceder a la pantalla completa e interactiva con buscador y filtros en el **[Dashboard](/public/dashboard.html)**.*"
            )

        await cl.Message(content=reply, elements=elements).send()
        return

    # 2. Flujo ReAct habitual con el agente financiero
    async with cl.Step(name="FinAgent analizando..."):
        response = await cl.make_async(agent.ask)(user_input, user_id=user_id)

    await cl.Message(content=response).send()

