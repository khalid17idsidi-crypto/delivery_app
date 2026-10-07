import os
import sys
import time
import base64
from typing import Optional, Dict, Any, List

import httpx
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Delivery Tracking & Routing API - FastAPI Backend")

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
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except Exception:
        return f"{lat}, {lng}"

def get_coords_from_address(address_text):
    try:
        if "الدار البيضاء" in address_text:
            query = address_text
        else:
            query = address_text + ", الدار البيضاء, المغرب"
        url = "https://nominatim.openstreetmap.org/search?q=" + requests.utils.quote(query) + "&format=json&limit=1"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
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
            raise HTTPException(status_code=400, detail="رقم هاتف المستلم الأول ورقم هاتف المستلم الثاني إلزاميان معاً لتأمين التسليم")
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
                    raise HTTPException(status_code=400, detail="يرجى تحديد وجهة التسليم بدقة على الخريطة أو كتابة عنوان صحيح")
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
        print("CRITICAL ERROR IN ACCEPT ORDER:", str(e))
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
        print("CRITICAL ERROR IN UPDATE DRIVER LOCATION:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wallet/topup")
async def wallet_topup(data: WalletTopupRequest):
    try:
        if data.amount < 30:
            raise HTTPException(status_code=400, detail="الحد الأدنى للشحن عبر التحويل البنكي CIH هو 30 درهم")
            
        bonus = 0.0
        if data.amount >= 100:
            bonus = 10.0
        elif data.amount >= 50:
            bonus = 4.0
            
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
        
        return {"status": "success", "message": "تم إرسال طلب الشحن بنجاح في انتظار مراجعة الأدمن", "data": db_res.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# واجهة تطبيق التوصيل الأساسية (للزبون والموصل)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl" id="htmlRoot">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title id="appMetaTitle">نتسخر ليك...كازا - خدمة التوصيل الذكية</title>

    <meta name="theme-color" content="#10b981" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;600;700;800;900&display=swap" rel="stylesheet" />

    <script src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet" />

    <script src="https://unpkg.com/@mapbox/mapbox-gl-language@1.0.1/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.39.8/dist/umd/supabase.min.js"></script>

    <style>
      :root {
        --primary: #10b981; --primary-dark: #059669; --bg-dark: #0f172a; --card-bg: #1e293b;
        --text-main: #f8fafc; --text-muted: #94a3b8; --border: rgba(255, 255, 255, 0.1);
        --danger: #ef4444; --warning: #f59e0b; --accent-green: #a3e635;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Tajawal", sans-serif; text-rendering: optimizeLegibility; }
      body {
        background: var(--bg-dark); color: var(--text-main); display: flex;
        justify-content: center; min-height: 100vh; overflow-y: auto; -webkit-tap-highlight-color: transparent;
        direction: rtl; text-align: right;
      }
      .app-container {
        width: 100%; max-width: 480px; min-height: 100vh; background: var(--bg-dark);
        position: relative; display: flex; flex-direction: column; padding-bottom: 70px;
      }
      .offline-banner { display: none; background: var(--danger); color: white; text-align: center; font-size: 11px; font-weight: bold; padding: 6px; z-index: 1002; }
      .location-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg-dark);
        z-index: 99999; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px; text-align: center;
      }
      .location-icon-box {
        width: 100px; height: 100px; background: rgba(16, 185, 129, 0.1); border: 2px solid var(--primary);
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 45px;
        margin-bottom: 20px; box-shadow: 0 0 25px rgba(16, 185, 129, 0.3); animation: pulse 2s infinite;
      }
      @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185
