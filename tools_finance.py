import contextvars
import datetime
import requests
from typing import Optional
from langchain_core.tools import tool

import database
import rag_finance

# Variable de contexto segura para identificar al usuario activo en Chainlit
current_user_id_var = contextvars.ContextVar("current_user_id", default=1)

def set_active_user_id(user_id: int):
    """Establece el ID del usuario actual para el hilo de ejecución."""
    current_user_id_var.set(user_id)

def get_active_user_id() -> int:
    """Obtiene el ID del usuario autenticado actual."""
    return current_user_id_var.get()

# ==============================================================================
# HERRAMIENTAS DE BASE DE DATOS (MOVIMIENTOS, BALANCES, METAS)
# ==============================================================================

@tool
def registrar_gasto_o_ingreso(tipo: str, categoria: str, monto: float, descripcion: str = "") -> str:
    """Registra un nuevo ingreso o gasto en la base de datos del usuario.
    
    :param tipo: 'ingreso' o 'gasto'.
    :param categoria: Categoría del movimiento (ej: 'Alquiler', 'Supermercado', 'Sueldo', 'Salidas', 'Servicios', 'Transporte', 'Farmacia').
    :param monto: Valor numérico positivo en pesos (ej: 45000).
    :param descripcion: Detalle opcional del movimiento (ej: 'Cena con amigos', 'Factura de luz').
    """
    user_id = get_active_user_id()
    try:
        tx_id = database.add_transaction(
            usuario_id=user_id,
            tipo=tipo.lower().strip(),
            categoria=categoria.strip(),
            monto=float(monto),
            descripcion=descripcion.strip()
        )
        return (
            f"✅ Movimiento registrado con éxito [ID #{tx_id}]:\n"
            f"- Tipo: {tipo.upper()}\n"
            f"- Categoría: {categoria}\n"
            f"- Monto: ${float(monto):,.2f}\n"
            f"- Detalle: {descripcion or 'Sin detalle'}"
        )
    except Exception as e:
        return f"Error al registrar movimiento: {str(e)}"

@tool
def fijar_o_ajustar_ingreso_mensual(accion: str, monto: float, descripcion: str = "") -> str:
    """Fija o ajusta el ingreso mensual (sueldo) del usuario en la base de datos y recalibra el presupuesto 50/30/20.
    IMPORTANTE: Úsalo siempre que el usuario indique cuánto gana en total o quiera subir/bajar sus ingresos mensuales.
    NUNCA registres un gasto para ajustar o bajar ingresos; usa SIEMPRE esta herramienta.
    
    :param accion: 'fijar' (para establecer el sueldo/ingreso total exacto, ej: 'gano 1.700.000' o 'fijá mis ingresos en 1.700.000'), 
                   'bajar' (para restar un importe de los ingresos existentes, ej: 'bajar mis ingresos en 1.000.000'), 
                   'subir' (para sumar un importe a los ingresos existentes).
    :param monto: El monto a fijar o el valor a subir/bajar (ej: 1700000 o 1000000).
    :param descripcion: Motivo o aclaración del ajuste (opcional).
    """
    user_id = get_active_user_id()
    act = accion.lower().strip()
    try:
        val = abs(float(monto))
        if act == "bajar":
            summary = database.adjust_monthly_income(user_id, -val, descripcion=descripcion or f"Reducción de ingreso en ${val:,.2f}")
            msg = f"📉 Se redujeron tus ingresos en **${val:,.2f}** sin alterar tus gastos."
        elif act == "subir":
            summary = database.adjust_monthly_income(user_id, val, descripcion=descripcion or f"Aumento de ingreso en ${val:,.2f}")
            msg = f"📈 Se aumentaron tus ingresos en **${val:,.2f}**."
        else: # 'fijar'
            summary = database.set_monthly_income(user_id, val, descripcion=descripcion or f"Sueldo fijado en ${val:,.2f}")
            msg = f"✅ Ingreso mensual fijado exitosamente en **${val:,.2f}**."
        
        nuevo_ingreso = summary['total_ingresos']
        saldo = summary['saldo_disponible']
        gastos = summary['total_gastos']
        
        return (
            f"{msg}\n\n"
            f"📋 **Nuevo Estado Contable del Mes ({summary['mes_año']}):**\n"
            f"• **Ingresos Totales:** `${nuevo_ingreso:,.2f}`\n"
            f"• **Gastos Totales:** `${gastos:,.2f}`\n"
            f"• **Saldo Disponible:** `${saldo:,.2f}`\n\n"
            f"🎯 **Nuevos límites 50/30/20 recalculados:**\n"
            f"• Necesidades (50%): hasta `${nuevo_ingreso * 0.5:,.2f}`\n"
            f"• Gustos (30%): hasta `${nuevo_ingreso * 0.3:,.2f}`\n"
            f"• Ahorro (20%): meta `${nuevo_ingreso * 0.2:,.2f}`"
        )
    except Exception as e:
        return f"Error al ajustar ingreso: {str(e)}"

@tool
def eliminar_o_corregir_movimiento(id_movimiento: int, accion: str, nuevo_monto: Optional[float] = None, nuevo_tipo: Optional[str] = None, nueva_descripcion: Optional[str] = None) -> str:
    """Permite anular (eliminar) o modificar una transacción registrada erróneamente en el historial.
    
    :param id_movimiento: El ID numérico de la transacción (puedes obtenerlo llamando a 'consultar_ultimos_movimientos').
    :param accion: 'eliminar' o 'modificar'.
    :param nuevo_monto: Si accion='modificar', el nuevo importe correcto.
    :param nuevo_tipo: Si accion='modificar', 'ingreso' o 'gasto' (opcional).
    :param nueva_descripcion: Nueva descripción si se desea cambiar (opcional).
    """
    user_id = get_active_user_id()
    act = accion.lower().strip()
    try:
        if act == "eliminar":
            ok = database.delete_transaction(user_id, int(id_movimiento))
            if ok:
                summary = database.get_monthly_summary(user_id)
                return f"🗑️ Movimiento #{id_movimiento} eliminado con éxito. Saldo actual disponible: ${summary['saldo_disponible']:,.2f}."
            else:
                return f"No se encontró un movimiento con ID #{id_movimiento} para tu usuario."
        elif act == "modificar":
            ok = database.update_transaction(user_id, int(id_movimiento), monto=nuevo_monto, tipo=nuevo_tipo, descripcion=nueva_descripcion)
            if ok:
                summary = database.get_monthly_summary(user_id)
                return f"✏️ Movimiento #{id_movimiento} modificado correctamente. Saldo actual disponible: ${summary['saldo_disponible']:,.2f}."
            else:
                return f"No se pudo modificar el movimiento #{id_movimiento}."
        else:
            return "Acción desconocida. Usa 'eliminar' o 'modificar'."
    except Exception as e:
        return f"Error al gestionar movimiento: {str(e)}"

@tool
def consultar_ultimos_movimientos(limite: int = 10) -> str:
    """Lista los últimos movimientos (ingresos y gastos) registrados con sus IDs numéricos, montos, tipos y fechas.
    Úsalo antes de modificar o eliminar una transacción para ubicar el ID exacto."""
    user_id = get_active_user_id()
    try:
        txs = database.get_recent_transactions(user_id, limit=limite)
        if not txs:
            return "No hay movimientos registrados recientemente."
        lines = [
            "📝 **Últimos Movimientos Registrados:**",
            "",
            "| ID | Tipo | Categoría | Monto | Fecha | Detalle |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        for t in txs:
            icono = "🟢" if t["tipo"] == "ingreso" else "🔴"
            lines.append(f"| `#{t['id']}` | {icono} {t['tipo'].capitalize()} | {t['categoria']} | `${t['monto']:,.2f}` | {t['fecha']} | {t['descripcion']} |")
        return "\n".join(lines)
    except Exception as e:
        return f"Error al consultar movimientos: {str(e)}"


@tool
def consultar_balance_y_presupuesto(mes_año: Optional[str] = None) -> str:
    """Consulta el balance financiero del usuario para el mes especificado,
    desglosando ingresos, gastos, saldo disponible y cumplimiento de la regla 50/30/20.
    
    :param mes_año: Opcional. Mes a consultar en formato 'YYYY-MM' (por defecto el mes actual).
    """
    user_id = get_active_user_id()
    try:
        summary = database.get_monthly_summary(user_id, mes_año)
        mes = summary["mes_año"]
        ingresos = summary["total_ingresos"]
        gastos = summary["total_gastos"]
        saldo = summary["saldo_disponible"]
        
        necesidades = summary["desglose_gastos"]["necesidades_50"]
        gustos = summary["desglose_gastos"]["gustos_30"]
        ahorro = summary["desglose_gastos"]["ahorro_inversion"]
        
        pct_nec = summary["porcentajes_actuales"]["necesidades_pct"]
        pct_gus = summary["porcentajes_actuales"]["gustos_pct"]
        pct_aho = summary["porcentajes_actuales"]["ahorro_pct"]

        res = [
            f"📊 **Diagnóstico Presupuestario ({mes})**",
            "",
            f'<div class="fin-meter-wrap">',
            f'  <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:5px; font-family:\'JetBrains Mono\', monospace;">',
            f'    <span style="color:#38BDF8;">🏠 Necesidades: {pct_nec}% (Meta: 50%)</span>',
            f'    <span style="color:#F59E0B;">🎉 Gustos: {pct_gus}% (Meta: 30%)</span>',
            f'    <span style="color:#10B981;">💰 Ahorro: {pct_aho}% (Meta: 20%)</span>',
            f'  </div>',
            f'  <div class="fin-meter-bar">',
            f'    <div class="fin-meter-seg necesidades" style="width:{min(pct_nec, 100)}%;"></div>',
            f'    <div class="fin-meter-seg gustos" style="width:{min(pct_gus, 100)}%;"></div>',
            f'    <div class="fin-meter-seg ahorro" style="width:{min(pct_aho, 100)}%;"></div>',
            f'  </div>',
            f'</div>',
            "",
            "| Rubro Presupuestario | Monto Actual | % del Ingreso | Recomendación |",
            "| :--- | :--- | :--- | :--- |",
            f"| 🏠 **Necesidades Básicas** | ${necesidades:,.2f} | **{pct_nec}%** | {'⚠️ Exceso >50%' if pct_nec > 50 else '✅ En regla (<=50%)'} |",
            f"| 🎉 **Gustos y Ocio** | ${gustos:,.2f} | **{pct_gus}%** | {'⚠️ Exceso >30%' if pct_gus > 30 else '✅ En regla (<=30%)'} |",
            f"| 💰 **Ahorro e Inversión** | ${ahorro:,.2f} | **{pct_aho}%** | {'✅ Excelente (>=20%)' if pct_aho >= 20 else '⚡ Meta a elevar'} |",
            "",
            f"• **Ingresos Totales:** `${ingresos:,.2f}` | **Gastos Totales:** `${gastos:,.2f}`",
            f"• **Saldo Disponible:** `${saldo:,.2f}`",
        ]

        if pct_nec > 50:
            res.append(f"\n> 💡 *Sugerencia contable:* Tus necesidades básicas superan el 50% de tus ingresos. Te sugerimos optimizar gastos fijos o recortar el segmento ocio para mantener tu capacidad de ahorro.")

        return "\n".join(res)
    except Exception as e:
        return f"Error al consultar balance: {str(e)}"

@tool
def gestionar_meta_ahorro(accion: str, nombre_meta: str, monto: float = 0.0, fecha_limite: Optional[str] = None) -> str:
    """Permite crear una nueva meta de ahorro o sumar dinero a una meta existente.
    
    :param accion: 'crear', 'depositar' o 'ver'.
    :param nombre_meta: Nombre de la meta (ej: 'Fondo de Emergencia', 'Vacaciones', 'Comprar Moto').
    :param monto: Monto objetivo (al crear) o monto a depositar (al depositar).
    :param fecha_limite: Fecha límite en formato 'YYYY-MM-DD' (opcional al crear).
    """
    user_id = get_active_user_id()
    act = accion.lower().strip()
    try:
        if act == "crear":
            goal_id = database.add_or_update_goal(user_id, nombre_meta, float(monto), fecha_limite)
            return f"🎯 Meta de ahorro '{nombre_meta}' creada con éxito [ID #{goal_id}] por un objetivo de ${float(monto):,.2f}."
        elif act == "depositar":
            ok = database.deposit_to_goal(user_id, nombre_meta, float(monto))
            if ok:
                return f"💰 Se acreditaron ${float(monto):,.2f} a la meta '{nombre_meta}'."
            else:
                return f"No se encontró una meta activa que coincida con '{nombre_meta}'."
        else:
            goals = database.get_goals(user_id)
            if not goals:
                return "No tienes metas de ahorro registradas todavía. Podés pedirme crear una (ej: Fondo de Emergencia)."
            out = [
                "🏆 **Tus Metas de Ahorro Activas:**",
                "",
                "| Meta de Ahorro | Acumulado | Objetivo | Progreso |",
                "| :--- | :--- | :--- | :--- |"
            ]
            for g in goals:
                pct = round((g["monto_acumulado"] / g["monto_objetivo"] * 100), 1) if g["monto_objetivo"] > 0 else 0
                out.append(f"| **{g['nombre_meta']}** | ${g['monto_acumulado']:,.2f} | ${g['monto_objetivo']:,.2f} | `{pct}%` |")
            return "\n".join(out)
    except Exception as e:
        return f"Error en gestión de metas: {str(e)}"

# ==============================================================================
# HERRAMIENTAS DE COTIZACIONES Y CÁLCULOS FINANCIEROS
# ==============================================================================

@tool
def obtener_cotizaciones_dolar_argentina() -> str:
    """Consulta en tiempo real las cotizaciones actuales de los distintos tipos de dólar en Argentina
    (Dólar Oficial, Dólar Blue, Dólar MEP, Dólar Tarjeta y Dólar Cripto) mediante API pública gratuita.
    """
    url = "https://dolarapi.com/v1/dolares"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            lines = [
                "💵 **Pizarra de Cotizaciones en Vivo (Argentina)**",
                "",
                "| Mercado / Tipo de Cambio | Compra | Venta | Actualización |",
                "| :--- | :--- | :--- | :--- |"
            ]
            for item in data:
                nombre = item.get("nombre", "")
                compra = item.get("compra", 0)
                venta = item.get("venta", 0)
                fecha = item.get("fechaActualizacion", "")[:10]
                lines.append(f"| **{nombre}** | `${compra:,.2f}` | `${venta:,.2f}` | `{fecha}` |")
            lines.append("\n*📡 Fuente: Datos oficiales de mercado vía DolarApi.com*")
            return "\n".join(lines)
    except Exception:
        pass

    # Fallback si no hay conexión externa a la API
    return (
        "💵 **Pizarra de Cotizaciones del Dólar (Estimación de Referencia)**\n\n"
        "| Mercado / Tipo de Cambio | Compra | Venta | Estado |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| **Dólar Oficial** | `$990.00` | `$1,030.00` | Referencia |\n"
        "| **Dólar Blue** | `$1,210.00` | `$1,230.00` | Referencia |\n"
        "| **Dólar MEP (Bolsa)** | `$1,180.00` | `$1,190.00` | Referencia |\n"
        "| **Dólar Cripto (USDT)** | `$1,200.00` | `$1,215.00` | Referencia |\n"
        "\n*(Aviso: No se pudo conectar a la API en vivo, mostrando cotizaciones de respaldo)*"
    )

@tool
def simular_rendimiento_inversion(monto_pesos: float, dias: int = 30, tasa_nominal_anual: float = 37.0) -> str:
    """Calcula el rendimiento estimado de una inversión a plazo fijo o fondo Money Market en pesos argentinos.
    
    :param monto_pesos: Capital a invertir en pesos (ej: 100000).
    :param dias: Plazo de la inversión en días (por defecto 30 días para plazo fijo tradicional).
    :param tasa_nominal_anual: Tasa Nominal Anual (TNA) en porcentaje (ej: 37.0).
    """
    try:
        tna = float(tasa_nominal_anual) / 100.0
        tasa_periodo = tna * (dias / 365.0)
        intereses_ganados = float(monto_pesos) * tasa_periodo
        monto_final = float(monto_pesos) + intereses_ganados
        tasa_mensual_pct = round((tasa_periodo * 100.0), 2)

        return (
            f"📈 **Simulación de Inversión ({dias} días a TNA {tasa_nominal_anual}%):**\n"
            f"• **Capital Inicial:** ${float(monto_pesos):,.2f}\n"
            f"• **Intereses Ganados:** ${intereses_ganados:,.2f}\n"
            f"• **Monto Final Estimado:** ${monto_final:,.2f}\n"
            f"• **Rendimiento Efectivo del Período:** {tasa_mensual_pct}%"
        )
    except Exception as e:
        return f"Error al simular inversión: {str(e)}"

# ==============================================================================
# HERRAMIENTA RAG (RECUPERACIÓN DE CONOCIMIENTO FINANCIERO)
# ==============================================================================

@tool
def consultar_educacion_financiera_rag(consulta: str) -> str:
    """Consulta la base de conocimiento de educación financiera para obtener explicaciones oficiales
    sobre conceptos de inversión en Argentina (CEDEARs, Obligaciones Negociables, Dólar MEP, Fondos Comunes, etc.).
    
    :param consulta: Término o duda financiera a consultar (ej: 'qué es un cedear', 'cómo armar fondo de emergencia').
    """
    docs = rag_finance.search_financial_knowledge(consulta, top_k=2)
    if not docs:
        return f"No se encontró un artículo específico sobre '{consulta}' en la base RAG local."

    out = ["📚 **Información de la Base de Conocimiento Financiero (RAG):**"]
    for d in docs:
        out.append(f"\n### {d['titulo']}\n{d['contenido']}")
    return "\n".join(out)

# ==============================================================================
# LISTA DE HERRAMIENTAS ACTIVAS PARA EL AGENTE FINANCIERO
# ==============================================================================
FINANCIAL_TOOLS = [
    registrar_gasto_o_ingreso,
    fijar_o_ajustar_ingreso_mensual,
    eliminar_o_corregir_movimiento,
    consultar_ultimos_movimientos,
    consultar_balance_y_presupuesto,
    gestionar_meta_ahorro,
    obtener_cotizaciones_dolar_argentina,
    simular_rendimiento_inversion,
    consultar_educacion_financiera_rag,
]
