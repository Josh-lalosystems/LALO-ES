from pydantic import BaseSettings


class MCPSettings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_WAIT_SELECTOR: str = "body"
    FRONTEND_TIMEOUT: int = 8

    class Config:
        env_file = ".env"


settings = MCPSettings()
