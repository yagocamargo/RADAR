from pydantic import BaseModel


class AdminStats(BaseModel):
    total_empresas: int
    total_contratos: int
    total_sinais: int
    total_usuarios: int
    alertas_nao_lidos: int


class RedisInfo(BaseModel):
    status: str
    used_memory_human: str | None = None


class AdminStatsResponse(BaseModel):
    stats: AdminStats
    redis: RedisInfo


class TriggerAgentResponse(BaseModel):
    task_id: str
    status: str
    agent: str
