from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UnidadeCreate(BaseModel):
    bloco: Optional[str] = None
    numero: str = Field(..., description="Número do apartamento ou casa")

class CondominioCreate(BaseModel):
    nome: str = Field(..., min_length=3)
    endereco: str
    unidades: List[UnidadeCreate] = Field(..., min_items=1, description="Lista de unidades a serem pré-cadastradas")

class SindicoCreate(BaseModel):
    email: EmailStr
    id_condominio: int = Field(..., description="ID do condomínio ao qual o síndico será vinculado (RN07)")