import os
import sys

# إجبار بايثون على قراءة مجلد المشروع الحالي ومجلد routes مباشرة
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routes.orders import router as orders_router
from routes.wallet import router as wallet_router

app = FastAPI(title="Delivery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين الـ Routers
app.include_router(orders_router)
app.include_router(wallet_router)

@app.get("/")
def serve_home():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

@app.get("/admin")
def serve_admin():
    return FileResponse(os.path.join(BASE_DIR, "templates", "admin.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
