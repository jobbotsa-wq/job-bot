from abc import ABC, abstractmethod


class BasePlatform(ABC):
    """Interfaz que toda plataforma de empleo debe implementar."""

    @abstractmethod
    def login(self, credentials: dict) -> bool:
        """Inicia sesión en la plataforma. Retorna True si exitoso."""
        pass

    @abstractmethod
    def search_jobs(self, filters: dict) -> list[dict]:
        """Busca ofertas según filtros. Retorna lista de jobs."""
        pass

    @abstractmethod
    def apply(self, job: dict, profile: dict) -> dict:
        """Aplica a una oferta. Retorna resultado con status y notas."""
        pass

    @abstractmethod
    def close(self):
        """Cierra la sesión y el browser."""
        pass
