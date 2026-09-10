from fastapi import FastAPI
from database import engine, Base

# 1. Importação dos modelos para registro no SQLAlchemy (necessário para o create_all funcionar)
import models.usuario
import models.chamado
import models.condominio
import models.categoria
import models.vinculo

# 2. Importação dos módulos de rotas (controllers)
from routers.router_auth import router_auth
from routers.router_admin import router_admin
from routers.router_chamados import router_chamados
from routers.router_vinculos import router_vinculos
from routers.router_categorias import router_categorias

# 3. Cria as tabelas no banco de dados automaticamente (recomendado apenas para ambiente de desenvolvimento)
Base.metadata.create_all(bind=engine)

# 4. Inicialização da aplicação FastAPI
app = FastAPI(
    title="Zelus API - Help Desk Condominial",
    description="API RESTful para gestão de manutenções condominiais",
    version="1.0.0"
)

# 5. Registro (plug-in) das rotas na aplicação principal
app.include_router(router_auth)
app.include_router(router_admin)
app.include_router(router_chamados)
app.include_router(router_vinculos)
app.include_router(router_categorias)