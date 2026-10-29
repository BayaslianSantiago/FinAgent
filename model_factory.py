import sys
import config

def get_llm(mode: str = None):
    """
    Retorna la instancia del modelo de lenguaje (LLM) según el modo especificado.
    
    :param mode: 'local' para Ollama o 'api' para Groq/OpenAI/etc. Si es None, usa config.MODE.
    :return: Instancia de BaseChatModel compatible con herramientas de LangChain.
    """
    target_mode = (mode or config.MODE).lower()

    if target_mode == "local":
        print(f"[ModelFactory] Inicializando LLM Local con Ollama...")
        print(f"               Modelo: {config.LOCAL_MODEL}")
        print(f"               Host: {config.LOCAL_BASE_URL}")
        
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.LOCAL_MODEL,
                base_url=config.LOCAL_BASE_URL,
                temperature=config.LOCAL_TEMPERATURE,
            )
        except ImportError:
            print("Error: Falta 'langchain-ollama'. Ejecuta: .\\venv\\Scripts\\pip install langchain-ollama", file=sys.stderr)
            raise

    elif target_mode == "api":
        provider_name = getattr(config, "PROVIDER", "api").upper()
        print(f"[ModelFactory] Inicializando LLM por API ({provider_name})...")
        print(f"               Modelo: {config.API_MODEL}")
        if config.API_BASE_URL:
            print(f"               Endpoint: {config.API_BASE_URL}")

        if not config.API_KEY:
            raise ValueError(
                "No se encontró una API Key para el modo 'api'.\n"
                "Agrega tu clave en el archivo .env:\n"
                "   GROQ_API_KEY=gsk_tu_clave_aqui\n"
                "o configúrala en config.py"
            )

        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.API_MODEL,
                api_key=config.API_KEY,
                base_url=config.API_BASE_URL,
                temperature=config.API_TEMPERATURE,
                max_tokens=config.API_MAX_TOKENS,
            )
        except ImportError:
            print("Error: Falta 'langchain-openai'. Ejecuta: .\\venv\\Scripts\\pip install langchain-openai", file=sys.stderr)
            raise

    else:
        raise ValueError(f"Modo no reconocido: '{target_mode}'. Opciones válidas: 'local' o 'api'")
