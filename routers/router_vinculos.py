from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.vinculo import VinculoCreate, VinculoAvaliar
from service import vinculo_service

def get_usuario_atual():
    # Placeholder dinâmico (O JWT depois vai ditar quem é o usuário)
    return {"id": 2, "perfil": "Sindico", "id_condominio": 4}

router_vinculos = APIRouter(prefix="/vinculos", tags=["Vínculos de Moradores"])

@router_vinculos.post("/solicitar", status_code=status.HTTP_201_CREATED, summary="RF05 - Solicitação de Cadastro do Morador")
def solicitar_vinculo(dados: VinculoCreate, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    # Na versão final, o "id_usuario" virá do token JWT.
    return vinculo_service.solicitar_vinculo(db, usuario["id"], dados)

@router_vinculos.get("/pendentes", summary="RF10 - Listar Cadastros Pendentes")
def listar_cadastros_pendentes(db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem ver pendências.")
    return vinculo_service.listar_pendentes(db, usuario["id_condominio"])

@router_vinculos.patch("/{id_vinculo}/avaliar", summary="RF10 - Aprovar ou Rejeitar Cadastro")
def avaliar_cadastro(id_vinculo: int, dados: VinculoAvaliar, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem avaliar cadastros.")
        
    vinculo = vinculo_service.avaliar_vinculo(db, id_vinculo, usuario["id"], dados.aprovado)
    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    return {"mensagem": f"Vínculo {'aprovado' if dados.aprovado else 'rejeitado'} com sucesso."}