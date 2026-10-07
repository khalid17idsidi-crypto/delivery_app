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
# 1. واجهة تطبيق التوصيل الأساسية (للزبون والموصل)
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
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(16, 185, 129, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
      }
      .location-overlay h2 { font-size: 18px; font-weight: 800; color: var(--primary); margin-bottom: 10px; }
      .location-overlay p { font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 25px; }
      .app-header {
        background: var(--card-bg); padding: 12px 16px; display: flex;
        justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); z-index: 1001; position: sticky; top: 0;
      }
      .app-title { font-size: 16px; font-weight: 900; color: var(--primary); display: flex; align-items: center; gap: 8px; cursor: pointer; }
      .hamburger-btn { background: transparent; border: none; color: var(--text-main); font-size: 24px; cursor: pointer; padding: 2px 8px; border-radius: 8px; }
      .driver-status-toggle {
        display: none; align-items: center; background: rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 3px 10px; cursor: pointer; font-size: 11px; font-weight: bold;
      }
      .driver-status-toggle.online { background: var(--primary); color: white; }
      .driver-status-toggle.offline { background: var(--danger); color: white; }
      .drawer-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px); z-index: 2000; opacity: 0; visibility: hidden; transition: all 0.3s ease;
      }
      .drawer-overlay.active { opacity: 1; visibility: visible; }
      .side-drawer {
        position: fixed; top: 0; bottom: 0; right: 0; width: 280px; max-width: 80%;
        background: var(--card-bg); z-index: 2001; box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        display: flex; flex-direction: column; transform: translateX(100%); transition: transform 0.3s ease-in-out;
      }
      .side-drawer.active { transform: translateX(0); }
      .drawer-header { padding: 20px 16px; background: rgba(16, 185, 129, 0.1); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 12px; }
      .drawer-avatar { width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--primary); object-fit: cover; background: var(--bg-dark); }
      .drawer-user-info { display: flex; flex-direction: column; gap: 2px; }
      .drawer-user-name { font-size: 14px; font-weight: 800; color: var(--primary); }
      .drawer-user-role { font-size: 10px; color: var(--text-muted); }
      .drawer-close-btn { background: transparent; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; margin-right: auto; }
      .drawer-menu { padding: 12px; display: flex; flex-direction: column; gap: 6px; flex: 1; overflow-y: auto; }
      .drawer-item {
        display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 12px;
        color: var(--text-main); font-size: 13px; font-weight: 700; cursor: pointer; border: none; background: transparent; width: 100%; text-align: right;
      }
      .drawer-item:hover, .drawer-item.active { background: rgba(16, 185, 129, 0.15); color: var(--primary); }
      .drawer-item.logout { color: var(--danger); margin-top: auto; border-top: 1px solid var(--border); }
      .lang-switcher-box { display: flex; gap: 6px; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid var(--border); margin-bottom: 8px; align-items: center; justify-content: space-between; }
      .lang-btn { background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; }
      .lang-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
      .content-area { flex: 1; position: relative; width: 100%; padding: 16px; }
      .view-panel { display: none; flex-direction: column; width: 100%; }
      .view-panel.active { display: flex; }
      .section-header { font-size: 14px; font-weight: 800; color: var(--primary); margin: 10px 0 8px; text-align: right; }
      .services-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
      .service-card {
        background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border); border-radius: 16px;
        padding: 12px 8px; text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center;
      }
      .service-card:hover { background: rgba(16, 185, 129, 0.1); border-color: var(--primary); }
      .service-card .emoji-badge { font-size: 28px; margin-bottom: 4px; }
      .service-card h4 { font-size: 12px; font-weight: 800; color: var(--text-main); }
      .hero-service-card {
        background: linear-gradient(160deg, rgba(16, 185, 129, 0.25), rgba(15, 23, 42, 0.95));
        border: 2px solid var(--primary); border-radius: 20px; padding: 14px 12px;
        display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px; margin-bottom: 12px;
      }
      .image-wrapper { width: 70px; height: 70px; border-radius: 14px; overflow: hidden; border: 2px solid var(--primary); display: flex; justify-content: center; align-items: center; background: var(--bg-dark); }
      .service-icon { width: 100%; height: 100%; object-fit: cover; }
      .promo-video-container { width: 100%; border-radius: 14px; overflow: hidden; border: 2px solid var(--primary); margin: 10px 0; background: #000; }
      .promo-video-container video { width: 100%; display: block; max-height: 220px; object-fit: cover; }
      .promo-banner {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(16, 185, 129, 0.2));
        border: 2px dashed var(--warning); border-radius: 16px; padding: 14px; margin-bottom: 15px; text-align: center;
      }
      .promo-banner h3 { color: var(--warning); font-size: 14px; font-weight: 900; margin-bottom: 6px; }
      .promo-banner p { font-size: 11px; color: var(--text-main); line-height: 1.5; margin-bottom: 10px; }
      .btn-order, .btn-submit {
        width: 100%; padding: 14px; background: var(--primary); color: white;
        border: none; border-radius: 14px; font-size: 13px; font-weight: 800; cursor: pointer; text-align: center;
      }
      .map-wrapper { position: relative; width: 100%; margin-bottom: 12px; }
      #map { width: 100%; height: 380px; border-radius: 14px; border: 2px solid var(--primary); cursor: pointer; }
      #clientTrackingMap { width: 100%; height: 400px; border-radius: 14px; border: 1px solid var(--border); margin-top: 10px; }
      #driverActiveMap { width: 100%; height: 350px; border-radius: 14px; border: 1px solid var(--border); margin-bottom: 10px; }
      .gps-btn {
        position: absolute; bottom: 12px; right: 12px; z-index: 1000; background: var(--card-bg);
        border: 1px solid var(--primary); color: var(--primary); padding: 6px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; cursor: pointer;
      }
      .compass-btn {
        position: absolute; top: 12px; right: 12px; z-index: 1000; background: var(--card-bg);
        border: 2px solid var(--warning); color: var(--warning); width: 45px; height: 45px; border-radius: 50%;
        font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer;
      }

      .field-group { margin-bottom: 12px; text-align: right; position: relative; }
      .field-group label { display: block; font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
      .field-group label span.required { color: var(--danger); font-weight: bold; }
      .field-group input, .field-group select, .field-group textarea {
        width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border);
        background: var(--card-bg); color: var(--text-main); font-size: 12px; outline: none; text-align: right; direction: rtl; font-family: "Tajawal", sans-serif;
      }
      .pin-instruction-box { background: rgba(16, 185, 129, 0.12); border: 1px solid var(--primary); border-radius: 12px; padding: 12px; margin-bottom: 10px; font-size: 12px; color: var(--text-main); text-align: center; line-height: 1.5; }
      .custom-toast-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); z-index: 999999; justify-content: center; align-items: center; padding: 20px; }
      .custom-toast-card { background: var(--card-bg); border: 1px solid var(--primary); border-radius: 16px; width: 100%; max-width: 320px; padding: 20px; text-align: center; }
      .indrive-order-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: right; }
      .card-top-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
      .price-badge-indrive { background: rgba(16, 185, 129, 0.15); color: var(--primary); font-size: 15px; font-weight: 900; padding: 4px 12px; border-radius: 10px; }
      .distance-tag { font-size: 11px; font-weight: bold; color: var(--warning); background: rgba(245, 158, 11, 0.1); padding: 4px 10px; border-radius: 8px; }
      .location-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; font-size: 12px; line-height: 1.5; color: var(--text-main); text-align: right; }
      .dot-point { width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
      .dot-point.pickup { background: #1e3a8a; box-shadow: 0 0 6px #1e3a8a; }
      .dot-point.delivery { background: var(--danger); box-shadow: 0 0 6px var(--danger); }
      .btn-indrive-action { width: 100%; margin-top: 12px; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 13px; font-weight: 800; cursor: pointer; text-align: center; }
      .nav-modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 999999; justify-content: center; align-items: center; padding: 20px; }
      .nav-modal-card { background: var(--card-bg); border: 2px solid var(--primary); border-radius: 18px; width: 100%; max-width: 320px; padding: 20px; text-align: center; }
      .perf-circles-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
      .perf-circle-card { background: linear-gradient(145deg, var(--card-bg), rgba(15, 23, 42, 0.8)); border: 1px solid var(--border); border-radius: 18px; padding: 14px 6px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .progress-ring-container { position: relative; width: 85px; height: 85px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
      .progress-ring-svg { width: 85px; height: 85px; transform: rotate(-90deg); }
      .progress-ring-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 7; }
      .progress-ring-fill { fill: none; stroke-width: 7; stroke-linecap: round; transition: stroke-dashoffset 0.6s ease; }
      .progress-ring-value-box { position: absolute; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; }
      .progress-ring-value { font-size: 14px; font-weight: 900; color: var(--text-main); }
      .progress-ring-icon { font-size: 14px; }
      .perf-circle-title { font-size: 11px; font-weight: 800; color: var(--text-muted); }
      .earnings-filter-tabs { display: flex; background: rgba(255,255,255,0.05); padding: 4px; border-radius: 12px; margin-bottom: 14px; gap: 4px; }
      .earnings-tab-btn { flex: 1; background: transparent; border: none; color: var(--text-muted); padding: 8px; font-size: 11px; font-weight: bold; border-radius: 8px; cursor: pointer; text-align: center; }
      .earnings-tab-btn.active { background: var(--primary); color: white; }
      .bonus-circles-container { display: flex; gap: 10px; justify-content: center; margin: 12px 0; }
      .bonus-circle {
        width: 85px; height: 85px; border-radius: 50%; border: 2px solid var(--warning);
        background: rgba(245, 158, 11, 0.1); display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; cursor: pointer; transition: all 0.2s ease;
      }
      .bonus-circle.active, .bonus-circle:hover { background: var(--warning); color: #000; box-shadow: 0 0 15px rgba(245, 158, 11, 0.5); transform: scale(1.05); }
      .bonus-circle .b-val { font-size: 13px; font-weight: 900; }
      .bonus-circle .b-desc { font-size: 10px; font-weight: bold; }
      .role-customer-item, .role-driver-item, .role-admin-item, .visitor-only-item { display: none; }
      .d-none-driver { display: block; }

      .security-box-warning {
        background: rgba(239, 68, 68, 0.15);
        border: 2px solid var(--danger);
        border-radius: 14px;
        padding: 14px;
        margin: 14px 0;
        text-align: right;
      }
      .security-box-warning h4 {
        color: var(--danger);
        font-size: 13px;
        font-weight: 900;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .security-box-warning p {
        font-size: 11px;
        line-height: 1.6;
        color: #fca5a5;
        margin-bottom: 10px;
      }
      .security-checkbox-label {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        font-size: 11px;
        font-weight: bold;
        color: var(--warning);
        cursor: pointer;
      }
      .security-checkbox-label input {
        width: 18px;
        height: 18px;
        accent-color: var(--danger);
        margin-top: 2px;
      }
    </style>
  </head>
  <body>
    <div class="app-container">
      <div class="offline-banner" id="offlineBanner">⚠️ أنت تعمل الآن في وضع غير متصل (Offline). سيتم حفظ طلباتك ومزامنتها فور عودة الإنترنت.</div>

      <div class="custom-toast-overlay" id="customToastOverlay">
        <div class="custom-toast-card">
          <h4 id="toastTitle" style="color: var(--primary); margin-bottom: 8px">تنبيه النظام</h4>
          <p id="toastMessage" style="font-size: 12px; margin-bottom: 14px"></p>
          <button class="btn-submit" onclick="closeCustomToast()" id="btnToastOk">حسناً 👍</button>
        </div>
      </div>

      <div class="nav-modal-overlay" id="navModalOverlay" onclick="closeNavModal(event)">
        <div class="nav-modal-card">
          <h3 style="color: var(--primary); margin-bottom: 6px; font-size: 15px;" id="navModalTitle">🧭 توجيه الموصل الفعلي</h3>
          <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 15px;" id="navModalSub">اختر الوجهة المباشرة بناءً على حالة الطلب الحقيقية:</p>
          <button class="btn-submit" style="margin-bottom: 8px; background: #1e3a8a;" onclick="openNavigatorApp('google', 'pickup')">📍 جوجل مابس: الذهاب للاستلام</button>
          <button class="btn-submit" style="margin-bottom: 12px; background: #ef4444;" onclick="openNavigatorApp('google', 'dropoff')">🎯 جوجل مابس: الذهاب للتسليم</button>
          <button class="btn-submit" style="margin-bottom: 8px; background: #0284c7;" onclick="openNavigatorApp('waze', 'pickup')">🚗 وايز: الذهاب للاستلام</button>
          <button class="btn-submit" style="margin-bottom: 12px; background: #f59e0b;" onclick="openNavigatorApp('waze', 'dropoff')">🏁 وايز: الذهاب للتسليم</button>
          <button class="btn-submit" style="background: transparent; color: var(--text-muted);" onclick="closeNavModal()">إلغاء</button>
        </div>
      </div>

      <div class="location-overlay" id="locationOverlay">
        <div class="location-icon-box">📍</div>
        <h2>تفعيل خدمة الموقع مطلوب</h2>
        <p>لتتمكن من استخدام التطبيق وخدمة التوصيل، يرجى السماح بتحديد موقعك الجغرافي الحالي بشكل دقيق.</p>
        <button class="btn-submit" onclick="requestUserLocationPermission()">📍 السماح وتفعيل الموقع الآن</button>
      </div>

      <header class="app-header">
        <div class="app-title" onclick="safeExecute(() => switchMainView('homeView'))">🚀 <span>نتسخر ليك...كازا</span></div>
        <div class="driver-status-toggle offline" id="driverStatusToggle" onclick="safeExecute(toggleDriverOnlineStatus)">
          <span id="driverStatusIcon">🔴</span>
          <span id="driverStatusText" style="margin-right: 4px">غير متصل</span>
