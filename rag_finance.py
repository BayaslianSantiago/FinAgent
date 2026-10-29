import re
import math
from typing import List, Dict, Any

# ==============================================================================
# BASE DE CONOCIMIENTO FINANCIERO (Curada para Argentina y Educación Financiera)
# ==============================================================================

KNOWLEDGE_DOCS = [
    {
        "id": "regla_50_30_20",
        "titulo": "La Regla de Presupuesto 50/30/20",
        "palabras_clave": ["50/30/20", "presupuesto", "gastos fijos", "necesidades", "gustos", "ahorro", "organizar sueldo"],
        "contenido": (
            "La Regla 50/30/20 es un marco simple para dividir los ingresos mensuales netos:\n"
            "- 50% Necesidades Básicas: Gastos fijos obligatorios para vivir (alquiler, expensas, servicios, comida esencial, transporte, salud, deudas obligatorias).\n"
            "- 30% Gustos y Calidad de Vida: Salidas, gastronomía, cine, streaming (Netflix, Spotify), ropa por gusto, hobbies y vacaciones.\n"
            "- 20% Ahorro e Inversión: Creación del Fondo de Emergencia, aportes a metas de largo plazo e inversión para el retiro.\n"
            "Consejo para Argentina: Si los gastos fijos superan el 50% por el alquiler o inflación, se recomienda achicar el rubro gustos al 20% o 15% para no sacrificar el ahorro."
        )
    },
    {
        "id": "fondo_de_emergencia",
        "titulo": "Fondo de Emergencia: El Primer Paso Financiero",
        "palabras_clave": ["fondo de emergencia", "imprevistos", "colchón", "liquidez", "primer paso", "seguridad"],
        "contenido": (
            "El Fondo de Emergencia es una suma de dinero reservada exclusivamente para imprevistos reales (desempleo, urgencia médica, reparación del auto, etc.).\n"
            "- Tamaño sugerido: Debe cubrir entre 3 y 6 meses de tus gastos fijos obligatorios.\n"
            "- Dónde guardarlo: Debe ser 100% líquido y accesible en el día. En Argentina no se recomienda dejarlo en una caja de ahorro en pesos porque la inflación lo destruye.\n"
            "- Instrumentos ideales: Fondos Comunes de Inversión (FCI) Money Market (rescate inmediato) o una porción en Dólar MEP / billete para conservar poder adquisitivo."
        )
    },
    {
        "id": "dolar_mep",
        "titulo": "Dólar MEP (Dólar Bolsa)",
        "palabras_clave": ["dolar mep", "dolar bolsa", "comprar dolares", "al30", "gd30", "parking", "dolar legal"],
        "contenido": (
            "El Dólar MEP (Medio Electrónico de Pagos) es una vía 100% legal, en blanco y sin límites para adquirir dólares en Argentina mediante la compra y venta de bonos soberanos (como el AL30 o GD30).\n"
            "- Mecánica: Comprás el bono en pesos (AL30) y lo vendés en su especie en dólares (AL30D).\n"
            "- Parking: Período obligatorio de permanencia del bono en custodia (usualmente 24hs hábiles) antes de venderlo.\n"
            "- Ventaja sobre el Dólar Blue: El MEP es formal, los dólares se acreditan directo en tu caja de ahorro bancaria en dólares, es más seguro y generalmente su cotización es más barata o transparente."
        )
    },
    {
        "id": "fci_money_market",
        "titulo": "Fondos Comunes de Inversión (FCI) Money Market y Billeteras Virtuales",
        "palabras_clave": ["fci", "money market", "fondos comunes", "mercado pago", "ualá", "billeteras virtuales", "tasa diaria"],
        "contenido": (
            "Los Fondos Money Market invierten en cuentas a la vista y plazos fijos de grandes bancos. Son los que usan las billeteras virtuales (Mercado Pago, Ualá, Naranja X, Personal Pay).\n"
            "- Liquidez: T+0 (inmediata, podés usar la plata los 7 días de la semana, 24hs).\n"
            "- Rendimiento: Pagan un interés diario basado en la Tasa Nominal Anual (TNA) de referencia.\n"
            "- Para qué sirven: Para el dinero del mes a mes (pagos de servicios, gastos diarios) para que no pierda valor mientras esperás la fecha de vencimiento."
        )
    },
    {
        "id": "cedears",
        "titulo": "CEDEARs: Invertir en Empresas Globales desde Argentina",
        "palabras_clave": ["cedear", "cedears", "acciones", "apple", "google", "sp500", "ccl", "invertir en pesos"],
        "contenido": (
            "Los CEDEARs (Certificados de Depósito Argentinos) representan acciones de empresas del exterior (como Apple, Google, Coca-Cola, Tesla o el índice S&P 500) pero se compran y venden en pesos en el mercado local (BYMA).\n"
            "- Doble factor de rendimiento:\n"
              "  1. La suba o baja de la acción en Wall Street.\n"
              "  2. La cotización del dólar Contado con Liquidación (CCL). Si el dólar sube, el CEDEAR sube en pesos automáticamente.\n"
            "- Perfil: Moderado a Arriesgado, pensado para mediano y largo plazo."
        )
    },
    {
        "id": "obligaciones_negociables",
        "titulo": "Obligaciones Negociables (ONs): Renta Fija Corporativa",
        "palabras_clave": ["obligaciones negociables", "ons", "renta fija", "bonos privados", "cupones en dolares", "ypf", "pampa"],
        "contenido": (
            "Las ONs son títulos de deuda que emiten empresas de primera línea (ej: YPF, Pampa Energía, Telecom, Arcor) para financiarse.\n"
            "- Funcionamiento: Le prestás plata a la empresa y te devuelve el capital más una tasa de interés pactada (usualmente entre 6% y 9% anual en dólares).\n"
            "- Cobro: Pagan renta periódica (cupones semestrales o trimestrales) que se deposita directamente en tu cuenta en dólares billete.\n"
            "- Perfil: Ideal para inversores conservadores o moderados que buscan ingresos periódicos en moneda dura."
        )
    },
    {
        "id": "interes_compuesto",
        "titulo": "El Poder del Interés Compuesto",
        "palabras_clave": ["interes compuesto", "reinversion", "largo plazo", "formula", "ahorro inteligente"],
        "contenido": (
            "El interés compuesto ocurre cuando las ganancias generadas por una inversión se reinvierten para generar nuevos intereses por sí mismas ('interés sobre interés').\n"
            "- Fórmula: Monto Final = Capital Inicial * (1 + tasa)^tiempo.\n"
            "- Consecuencia: En el corto plazo el crecimiento parece lineal, pero a partir de los 5 a 10 años la curva se vuelve exponencial.\n"
            "- Regla de oro: El factor más poderoso no es la cantidad de dinero, sino el tiempo. Empezar joven con montos chicos supera a empezar tarde con montos grandes."
        )
    },
    {
        "id": "monotributo_y_finanzas",
        "titulo": "Gestión Financiera para Monotributistas y Freelancers",
        "palabras_clave": ["monotributo", "freelance", "independiente", "ingresos variables", "separar cuentas", "arca", "afip"],
        "contenido": (
            "Los trabajadores independientes enfrentan la dificultad de tener ingresos variables mes a mes:\n"
            "- Regla 1: Sueldo Fijo Personal. Asignate un sueldo mensual constante. En los meses de facturación récord, guardá el excedente en una reserva para compensar los meses flojos.\n"
            "- Regla 2: Separar Cuentas. Nunca mezcles la plata del negocio con los gastos del hogar.\n"
            "- Regla 3: Previsión impositiva y jubilatoria. Destiná automáticamente el porcentaje de Monotributo, Ingresos Brutos (IIBB) y seguro al momento de emitir cada factura."
        )
    }
]

# ==============================================================================
# MOTOR RAG (Búsqueda Semántica Local por Relevancia y TF-IDF)
# ==============================================================================

def tokenize(text: str) -> List[str]:
    """Limpia y tokeniza palabras en minúsculas ignorando puntuación."""
    return re.findall(r'\b[a-záéíóúüñ0-9/]{3,}\b', text.lower())

def search_financial_knowledge(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Busca los documentos conceptuales más relevantes para la consulta del usuario.
    Retorna los fragmentos de conocimiento que mejor responden a la pregunta.
    """
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    scored_docs = []

    for doc in KNOWLEDGE_DOCS:
        score = 0.0
        # Ponderación por palabras clave directas
        doc_keywords = set(doc["palabras_clave"])
        matches_keywords = query_tokens.intersection(doc_keywords)
        score += len(matches_keywords) * 4.0

        # Ponderación por título
        title_tokens = set(tokenize(doc["titulo"]))
        matches_title = query_tokens.intersection(title_tokens)
        score += len(matches_title) * 2.5

        # Ponderación por contenido
        content_tokens = tokenize(doc["contenido"])
        for token in query_tokens:
            count = content_tokens.count(token)
            if count > 0:
                score += 1.0 + math.log(count)

        if score > 0:
            scored_docs.append((score, doc))

    # Ordenar por puntaje descendente
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored_docs[:top_k]]
