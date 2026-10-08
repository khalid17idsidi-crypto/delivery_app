import os
import sys
import time
from typing import Optional, Dict, Any, List

import httpx
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ربط مجلد الملفات الثابتة (إذا كان اسم المجلد لديك static أو public)
app.mount(
    "/static", StaticFiles(directory="templates"), name="static"
)

from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Delivery Tracking & Routing API - Casablanca")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = "https://cauujrnxtqswjzqhphyq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODM0MTA0MywiZXhwIjoyMTAzOTE3MDQzfQ.17AG1uMHj14ZNVuzp56-9_Z2KYeG50Oo3k__kDbhUok"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# قراءة الملفات من مجلد templates بأمان
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def get_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        # محاولة قراءة الملف من نفس المجلد في حال عدم استخدام مجلد فرعي
        alt_path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(alt_path):
            with open(alt_path, "r", encoding="utf-8") as f:
                return f.read()
        raise HTTPException(status_code=404, detail=f"الملف {filename} غير موجود داخل مجلد templates")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class OrderRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    dropoff_address_text: Optional[str] = ""
    user_id: Optional[str] = "user_123"
    customer_name: Optional[str] = "أمين"
    customer_phone: Optional[str] = "0600000000"
    recipient_phone: str
    recipient_phone_secondary: str
    package_type: Optional[str] = "طرد"
    notes: Optional[str] = ""
    security_accepted: bool = False

class AcceptOrderRequest(BaseModel):
    order_id: str
    driver_id: Optional[str] = None
    courier_id: Optional[str] = None

class DriverLocationUpdate(BaseModel):
    order_id: str
    driver_id: str
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start_lng: float
    start_lat: float
    end_lng: float
    end_lat: float

class WalletTopupRequest(BaseModel):
    user_id: str
    amount: float
    receipt_url: str = "https://via.placeholder.com/150"

def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryAppCasablanca/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except Exception:
        return f"{lat}, {lng}"

def get_coords_from_address(address_text):
    try:
        query = address_text if "الدار البيضاء" in address_text else address_text + ", الدار البيضاء, المغرب"
        url = "https://nominatim.openstreetmap.org/search?q=" + requests.utils.quote(query) + "&format=json&limit=1"
        headers = {'User-Agent': 'DeliveryAppCasablanca/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        if res and len(res) > 0:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception as e:
        print("Geocoding error in backend:", e)
    return None, None

@app.post("/api/get-live-route")
async def get_live_route(data: RouteRequest):
    url = f"http://router.project-osrm.org/route/v1/driving/{data.start_lng},{data.start_lat};{data.end_lng},{data.end_lat}?overview=full&geometries=geojson"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="فشل في حساب المسار الجغرافي")
            
            route_data = response.json()
            if not route_data.get("routes"):
                raise HTTPException(status_code=404, detail="لا يوجد مسار متاح بين النقطتين")
            
            routejson = route_data["routes"][0]["geometry"]
            distance = route_data["routes"][0]["distance"] / 1000.0
            duration = route_data["routes"][0]["duration"] / 60.0

            return {
                "status": "success",
                "distance_km": round(distance, 2),
                "duration_mins": round(duration, 1),
                "route_geometry": routejson
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        if not order.security_accepted:
            raise HTTPException(status_code=400, detail="الموافقة على الشروط الأمنية وحق التبليغ للشرطة إلزامية لإنشاء الطلب")
        if not order.recipient_phone or not order.recipient_phone_secondary:
            raise HTTPException(status_code=400, detail="رقما هاتف المستلم إلزاميان معاً لتأمين التسليم")
        if not order.pickup_lat or not order.pickup_lng:
            raise HTTPException(status_code=400, detail="موقع الاستلام عبر GPS غير متوفر")
            
        pickup_address = get_address_from_coords(order.pickup_lat, order.pickup_lng)
        
        final_dropoff_lat = order.dropoff_lat
        final_dropoff_lng = order.dropoff_lng
        dropoff_address = ""

        if not final_dropoff_lat or not final_dropoff_lng:
            if order.dropoff_address_text:
                lat, lng = get_coords_from_address(order.dropoff_address_text)
                if lat and lng:
                    final_dropoff_lat = lat
                    final_dropoff_lng = lng
                    dropoff_address = order.dropoff_address_text
                else:
                    raise HTTPException(status_code=400, detail="يرجى تحديد وجهة التسليم بدقة على الخريطة")
            else:
                raise HTTPException(status_code=400, detail="الرجاء تحديد نقطة التسليم على الخريطة أولاً")
        else:
            dropoff_address = get_address_from_coords(final_dropoff_lat, final_dropoff_lng)

        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{order.pickup_lng},{order.pickup_lat};{final_dropoff_lng},{final_dropoff_lat}?overview=full&geometries=geojson"
        
        distance_km = 2.0
        route_geometry = {
            "type": "LineString",
            "coordinates": [
                [order.pickup_lng, order.pickup_lat],
                [final_dropoff_lng, final_dropoff_lat]
            ]
        }

        try:
            response = requests.get(osrm_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("routes"):
                    distance_meters = data['routes'][0]['distance']
                    distance_km = round(distance_meters / 1000.0, 2)
                    route_geometry = data['routes'][0]['geometry']
        except Exception:
            pass
        
        if distance_km < 3.0:
            total_price = 20.0
        elif 3.0 <= distance_km <= 9.0:
            total_price = 25.0
        elif 9.0 < distance_km <= 12.0:
            total_price = 30.0
        else:
            total_price = 30.0 + ((distance_km - 12.0) * 2.5)
            
        total_price = round(total_price, 2)
        
        order_data = {
            "customer_id": order.user_id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "recipient_phone": order.recipient_phone,
            "recipient_phone_secondary": order.recipient_phone_secondary,
            "package_type": order.package_type,
            "notes": order.notes,
            "pickup_address": pickup_address,
            "dropoff_address": dropoff_address,
            "pickup_lat": order.pickup_lat,
            "pickup_lng": order.pickup_lng,
            "dropoff_lat": final_dropoff_lat,
            "dropoff_lng": final_dropoff_lng,
            "distance_km": distance_km,
            "price_mad": total_price,
            "status": "pending",
            "route_path": route_geometry
        }
        
        db_response = supabase.table("orders").insert(order_data).execute()
        
        return {
            "status": "success",
            "message": "تم حساب المسار وتخزين الطلب بنجاح",
            "data": {
                "distance_km": distance_km,
                "price_mad": total_price,
                "pickup_address": pickup_address,
                "dropoff_address": dropoff_address,
                "route_path": route_geometry,
                "order_details": db_response.data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print("CRITICAL ERROR IN CREATE ORDER:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/accept-order")
def accept_order(data: AcceptOrderRequest):
    try:
        the_driver_id = data.driver_id or data.courier_id
        if not the_driver_id:
            raise HTTPException(status_code=400, detail="معرف الموصل مفقود")

        db_response = supabase.table("orders").update({
            "status": "assigned",
            "driver_id": the_driver_id
        }).eq("id", data.order_id).execute()
        
        return {
            "status": "success",
            "message": "تم قبول الطلب بنجاح",
            "data": db_response.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-driver-location")
def update_driver_location(data: DriverLocationUpdate):
    try:
        db_response = supabase.table("orders").update({
            "driver_lat": data.lat,
            "driver_lng": data.lng
        }).eq("id", data.order_id).execute()
        
        return {
            "status": "success",
            "message": "تم تحديث موقع الموصل بنجاح",
            "data": db_response.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/topup")
async def wallet_topup(data: WalletTopupRequest):
    try:
        if data.amount < 30:
            raise HTTPException(status_code=400, detail="الحد الأدنى للشحن هو 30 درهم")
            
        bonus = 10.0 if data.amount >= 100 else (4.0 if data.amount >= 50 else 0.0)
        total_credited = data.amount + bonus
        
        topup_data = {
            "driver_id": data.user_id,
            "amount": data.amount,
            "bonus": bonus,
            "total_credited": total_credited,
            "receipt_url": data.receipt_url,
            "status": "pending"
        }
        
        db_res = supabase.table("wallet_topups").insert(topup_data).execute()
        return {"status": "success", "message": "تم إرسال طلب الشحن بنجاح", "data": db_res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return HTMLResponse(content=get_template("index.html"))

@app.get("/admin", response_class=HTMLResponse)
def serve_admin():
    return HTMLResponse(content=get_template("admin.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
