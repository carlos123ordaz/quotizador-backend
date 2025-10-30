from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import connect_to_mongo, close_mongo_connection
from routes.product_routes import router as product_router
from routes.report_routes import router as report_router
from routes.auth_routes import router as auth_router
from routes.employee_routes import router as employee_router
from routes.history_routes import router as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    print("Aplicación iniciada")
    yield
    await close_mongo_connection()
    print("Aplicación detenida")
    
app = FastAPI(
    title="Excel Manager API",
    description="API para gestión de productos, empleados, reportes Excel y integración con Bitrix CRM",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(product_router)
app.include_router(report_router)
app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(history_router)

@app.get("/")
def root():
    return {"message": "API de Productos funcionando 🚀"}
