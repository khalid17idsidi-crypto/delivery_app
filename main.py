import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# 1. تثبيت المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.getcwd())

# 2. فحص الملفات المتاحة وطباعتها في الـ Logs
try:
    print("=== FILES IN BASE DIR ===", os.listdir(BASE_DIR), flush=True)
except Exception as e:
    print("Could not list dir:", e, flush=True)

# 3. محاولة استيراد مرنة (سواء كان في المجلد الرئيسي أو داخل routes)
try:
    from orders import router as orders_router
except ModuleNotFoundError:
    try:
        from routes.orders import router as orders_router
    except ModuleNotFoundError:
        import importlib.util
        possible_path = os.path.join(BASE_DIR, "routes", "orders.py")
        if os.path.exists(possible_path):
            spec = importlib.util.spec_from_file_location("orders", possible_path)
            orders_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(orders_module)
            orders_router = orders_module.router
        else:
            raise

try:
    from wallet import router as wallet_router
except ModuleNotFoundError:
    try:
        from routes.wallet import router as wallet_router
    except ModuleNotFoundError:
        import importlib.util
        possible_path = os.path.join(BASE_DIR, "routes", "wallet.py")
        if os.path.exists(possible_path):
            spec = importlib.util.spec_from_file_location("wallet", possible_path)
            wallet_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wallet_module)
            wallet_router = wallet_module.router
        else:
            raise

# 4. إعداد التطبيق
app = FastAPI(title="Delivery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. ربط الـ Routers
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
