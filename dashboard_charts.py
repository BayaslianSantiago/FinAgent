import plotly.graph_objects as go
import database
from typing import Dict, Any, List

def generate_503020_donut_chart(summary: Dict[str, Any]) -> go.Figure:
    """Genera un gráfico de dona interactivo en Plotly para la regla 50/30/20 con estética Obsidian/Gold."""
    necesidades = summary["desglose_gastos"]["necesidades_50"]
    gustos = summary["desglose_gastos"]["gustos_30"]
    ahorro = max(0.0, summary["saldo_disponible"] + summary["desglose_gastos"]["ahorro_inversion"])

    labels = ["🏠 Necesidades (50%)", "🎉 Gustos (30%)", "💰 Ahorro / Saldo (20%)"]
    values = [necesidades, gustos, ahorro]
    colors = ["#38BDF8", "#F59E0B", "#10B981"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        marker=dict(colors=colors, line=dict(color='#090E17', width=2)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Monto: $%{value:,.2f}<br>Porcentaje: %{percent}<extra></extra>",
        textposition="outside",
        textfont=dict(family="Plus Jakarta Sans, sans-serif", size=12, color="#E2E8F0")
    )])

    fig.update_layout(
        title=dict(
            text=f"<b>Distribución Presupuestaria 50/30/20 ({summary.get('mes_año', '')})</b>",
            font=dict(family="Playfair Display, serif", size=17, color="#D4AF37"),
            x=0.5,
            xanchor="center"
        ),
        paper_bgcolor="rgba(13, 21, 36, 0.8)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(family="Plus Jakarta Sans", size=11, color="#94A3B8")
        ),
        margin=dict(l=20, r=20, t=50, b=50),
        height=360
    )

    return fig

def generate_category_bar_chart(user_id: int) -> go.Figure:
    """Genera un gráfico de barras horizontales interactivo con el desglose de gastos por categoría."""
    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT categoria, SUM(monto) as total
            FROM movimientos
            WHERE usuario_id = ? AND tipo = 'gasto'
            GROUP BY categoria
            ORDER BY total ASC
        """, (user_id,))
        rows = cursor.fetchall()

    if not rows:
        cats = ["Sin gastos"]
        totals = [0.0]
    else:
        cats = [r["categoria"] for r in rows]
        totals = [float(r["total"]) for r in rows]

    fig = go.Figure(data=[go.Bar(
        x=totals,
        y=cats,
        orientation='h',
        marker=dict(
            color="#D4AF37",
            line=dict(color="#F3E5AB", width=1)
        ),
        hovertemplate="<b>%{y}</b>: $%{x:,.2f}<extra></extra>",
        text=[f"${v:,.0f}" for v in totals],
        textposition="auto",
        textfont=dict(family="JetBrains Mono", size=11, color="#090E17")
    )])

    fig.update_layout(
        title=dict(
            text="<b>Gastos Acumulados por Categoría</b>",
            font=dict(family="Playfair Display, serif", size=17, color="#D4AF37"),
            x=0.5,
            xanchor="center"
        ),
        paper_bgcolor="rgba(13, 21, 36, 0.8)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(family="JetBrains Mono", size=10, color="#94A3B8"),
            tickprefix="$"
        ),
        yaxis=dict(
            tickfont=dict(family="Plus Jakarta Sans", size=11, color="#E2E8F0")
        ),
        margin=dict(l=30, r=30, t=50, b=30),
        height=320
    )

    return fig
