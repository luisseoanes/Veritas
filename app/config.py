"""Configuracion central. Lee variables de entorno / .env una sola vez."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Proveedor de LLM: mock | gemini
    llm_provider: str = "mock"

    gemini_api_key: str = ""
    # gemini-2.5-flash devuelve 404 en cuentas nuevas ("no longer available to
    # new users"). Se fija un modelo estable y NO un alias '-latest': un alias
    # puede cambiar de version solo, en medio de la demo.
    gemini_model: str = "gemini-3.6-flash"

    # --- Retrieval (RAG) ---
    # Vacio = sigue a llm_provider. Ponerlo explicito solo para desacoplarlos
    # (ej. LLM en gemini pero retrieval en mock durante desarrollo).
    embedding_provider: str = ""
    gemini_embedding_model: str = "gemini-embedding-001"
    # 768 en vez de las 3072 nativas: recorta memoria y latencia sin perdida
    # medible a esta escala de corpus. gemini-embedding-001 soporta el truncado.
    embedding_dim: int = 768
    chroma_path: str = "data/generated/chroma"
    retrieval_top_k: int = 4

    # Limite de pasos del loop del agente (evita loops infinitos de tools)
    max_agent_steps: int = 8

    brand: str = "WEG"

    # Token compartido para las rutas de administrador (/admin/*, /demo/*).
    # Un solo token, sin usuarios: cubre la distincion cliente/admin de la demo
    # sin la complejidad de JWT/OAuth. Vive en .env, nunca en el codigo.
    # Vacio = el servidor niega TODA ruta admin (fail-closed); B5 lo convierte
    # en un fallo de arranque para que no pase desapercibido.
    admin_token: str = ""


settings = Settings()
