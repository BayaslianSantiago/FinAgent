# 📊 FinAgent - Asesor Financiero Personal Inteligente

**Proyecto Integrador Final**  
*Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial* — **ISFT N° 197**  
Cátedra: *PP: Proyecto Integrador* | Docente: *Prof. Alejandro Luis Bonavita*

FinAgent es un agente de Inteligencia Artificial que democratiza la educación financiera y la planificación presupuestaria en Argentina mediante una interfaz web moderna en **Chainlit**, un motor de razonamiento autónomo con **LangGraph**, llamadas a herramientas de mercado en tiempo real y persistencia relacional con **SQLite**.

---

## 📁 Estructura Modular del Proyecto

```text
agente/
├── docs/                 # Documentación y plantilla base del Proyecto Integrador
│   └── TSCIA - PP Proyecto Integrador - Plantilla de documento base (1).docx
├── .chainlit/            # Configuración de tema y widgets de Chainlit
├── .env                  # Variables de entorno y API keys locales (ignorado en git)
├── .env.example          # Plantilla para compartir variables de entorno
├── app.py                # Punto de entrada de la aplicación web (Chainlit + Auth)
├── agent.py              # Agente ReAct (LangGraph + Prompt financiero especializado)
├── model_factory.py      # Fábrica de LLMs (Groq API en la nube u Ollama local)
├── database.py           # Capa de datos relacional SQLite (usuarios, 50/30/20, metas)
├── tools_finance.py      # Herramientas del agente (DB, DolarApi, simulador, RAG)
├── rag_finance.py        # Base de conocimiento financiero local (RAG)
├── config.py             # Configuración central del sistema
├── chainlit.md           # Pantalla de bienvenida de Chainlit
├── finanzas.db           # Base de datos SQLite
└── requirements.txt      # Dependencias del proyecto
```

---

## 🏗️ Arquitectura y Flujo de Información

```mermaid
graph TD
    User["👤 Usuario en Navegador"] -->|Login seguro (Hash PBKDF2/SHA-256)| Chainlit["🖥️ Interfaz Web (app.py)"]
    Chainlit --> Agent["🧠 FinAgent (agent.py - LangGraph ReAct)"]
    
    subgraph Modelos ["🤖 Motor de Inteligencia (model_factory.py)"]
        Agent --> Groq["☁️ Groq Cloud API (Por Defecto - Ultra Veloz)"]
        Agent --> Ollama["🏠 Ollama Llama 3.2 (Offline Opcional)"]
    end

    subgraph Herramientas ["🛠️ Herramientas Financieras (tools_finance.py)"]
        Agent --> DBTool["🗄️ SQLite (database.py: Movimientos, 50/30/20, Metas)"]
        Agent --> DolarAPI["💵 DolarApi (Cotizaciones en vivo)"]
        Agent --> SimTool["📈 Simulador Plazo Fijo / Inversión"]
        Agent --> RAGTool["📚 RAG Local (rag_finance.py: Glosario BCRA, CEDEARs, ONs)"]
    end
```

---

## 🗄️ Modelo de Base de Datos Relacional (`finanzas.db`)

1. **`usuarios`**: Almacena credenciales con hashing seguro PBKDF2/SHA-256 + salt y perfil de riesgo (*Conservador*, *Moderado*, *Arriesgado*).
2. **`presupuestos_mensuales`**: Foto macro del mes aplicando la **Regla 50/30/20**.
3. **`movimientos`**: Registro granular de ingresos y gastos diarios clasificados automáticamente en *necesidad*, *gusto* o *ahorro*.
4. **`metas_ahorro`**: Seguimiento de objetivos con porcentaje de avance (ej. *Fondo de Emergencia*).
5. **`contexto_ia`**: Memoria cualitativa a largo plazo del perfil y situación del usuario.

---

## 🚀 Puesta en Marcha

Para iniciar el servidor web interactivo ejecuta:

```powershell
.\venv\Scripts\chainlit run app.py -w
```

Abre tu navegador en: **`http://localhost:8000`**

### 🔑 Credenciales Demo preconfiguradas:
* **Usuario:** `demo`
* **Contraseña:** `demo123`

---

## 💡 Ejemplos de uso en el Chat:
* **Registrar gastos:** *"Anotá 45.000 de compras en el supermercado"*
* **Ver balance:** *"¿Cómo voy este mes con mi presupuesto 50/30/20?"*
* **Dólar en tiempo real:** *"¿A cuánto cotizan el Dólar Blue y MEP hoy?"*
* **Simulación:** *"¿Cuánto gano si coloco 250.000 pesos en un plazo fijo a 30 días?"*
* **Educación Financiera (RAG):** *"¿Qué es un CEDEAR y cómo me protege de la devaluación?"*
* **Metas de ahorro:** *"¿Cómo va mi meta de Fondo de Emergencia?"*
