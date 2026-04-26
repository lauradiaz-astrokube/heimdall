from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import settings
from app.routers import health, catalog, requests, grants

# ---------------------------------------------------------------------------
# Aplicación FastAPI — HeimdALL Backend
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HeimdALL API",
    description="Portal de elevación de privilegios Just-In-Time integrado con AWS IAM Identity Center",
    version="0.1.0",
)

# CORS: permite que el frontend (React) llame a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(catalog.router)
app.include_router(requests.router)
app.include_router(grants.router)

# ---------------------------------------------------------------------------
# Punto de entrada para AWS Lambda (via Mangum)
# Mangum traduce los eventos de API Gateway al formato ASGI que entiende FastAPI
# ---------------------------------------------------------------------------
lambda_handler = Mangum(app, lifespan="off")


# ---------------------------------------------------------------------------
# Punto de entrada local (uvicorn) para desarrollo
# Ejecutar con: uvicorn app.main:app --reload
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
