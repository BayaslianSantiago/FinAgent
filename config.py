import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# ==============================================================================
# CONFIGURACIÓN PRINCIPAL
# ==============================================================================
# Opciones disponibles para MODE: "local" | "api"
# ==============================================================================
MODE = os.getenv("AGENT_MODE", "local").lower()  # "local" o "api"

# ------------------------------------------------------------------------------
# Configuración para Modo Local (Ollama)
# ------------------------------------------------------------------------------
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
LOCAL_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LOCAL_TEMPERATURE = 0.2

# ------------------------------------------------------------------------------
# Configuración para Modo API (Groq por defecto, o OpenAI)
# ------------------------------------------------------------------------------
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

if GROQ_KEY:
    PROVIDER = "groq"
    API_KEY = GROQ_KEY
    API_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    API_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
else:
    PROVIDER = "openai"
    API_KEY = OPENAI_KEY
    API_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    API_BASE_URL = os.getenv("OPENAI_BASE_URL", None)

API_TEMPERATURE = 0.2
API_MAX_TOKENS = int(os.getenv("API_MAX_TOKENS", "4000"))


