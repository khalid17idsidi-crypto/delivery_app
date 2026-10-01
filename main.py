import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from supabase import create_client, Client

app = FastAPI(title="Delivery Tracking & Routing API - Python Backend")

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

MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "pk.eyJ1IjoiaWRzaWRpIiwiYSI6ImNtdTJscHkybjAwbW8yeXF1cXFhdXozaWMifQ.FDKkwkz9kdug1cghlLNChw")

class OrderRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float = None
    dropoff_lng: float = None
    dropoff_address_text: str = ""
    user_id: str = "user_123"
    customer_name: str = "أمين"
    customer_phone: str = "0600000000"
    recipient_phone: str = "0700000000"
    package_type: str = "طرد"
    notes: str = ""

class AcceptOrderRequest(BaseModel):
    order_id: str
    driver_id: str = None
    courier_id: str = None

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

def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except:
        return f"{lat}, {lng}"

def get_coords_from_address(address_text):
    """
    بحث دقيق وشامل عبر OpenStreetMap يغطي الدار البيضاء الكبرى بكافة أحيائها وشوارعها بدون أي قيود ضيقة
    """
    try:
        clean_text = address_text.strip()
        if not clean_text:
            return None, None

        headers = {'User-Agent': 'DeliveryApp/1.0'}
        
        # قائمة استعلامات ذكية تجرب عدة صيغ لضمان إيجاد العنوان في الدار البيضاء الكبرى بدقة
        queries = [
            f"{clean_text}, الدار البيضاء, المغرب",
            f"{clean_text}, Casablanca, Morocco",
            clean_text
        ]
        
        # نطاق جغرافي واسع ومناسب للدار البيضاء الكبرى (يشمل المحمدية، عين الشق، البرنوصي، سيدي مومن، إلخ)
        casablanca_viewbox = "-7.85,33.30,-7.20,33.80"

        for q in queries:
            url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(q)}&format=json&limit=1&countrycodes=ma&viewbox={casablanca_viewbox}&bounded=0"
            res = requests.get(url, headers=headers, timeout=4).json()
            if res and len(res) > 0:
                return float(res[0]['lat']), float(res[0]['lon'])
                
    except Exception as e:
        print("Geocoding error in backend:", e)
        
    return None, None

@app.post("/api/get-live-route")
async def get_live_route(data: RouteRequest):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{data.start_lng},{data.start_lat};{data.end_lng},{data.end_lat}?geometries=geojson&overview=full&access_token={MAPBOX_ACCESS_TOKEN}"
    
    async with httpx.AsyncClient() as client:
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

@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        if not order.pickup_lat or not order.pickup_lng:
            raise HTTPException(status_code=400, detail="موقع الاستلام عبر GPS غير متوفر، يرجى تفعيل الـ GPS وتحديد النقطة بدقة")
            
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
                    raise HTTPException(status_code=400, detail="عذراً، لم نتمكن من إيجاد هذا العنوان في الدار البيضاء الكبرى. يرجى كتابة اسم الشارع أو الحي بوضوح، أو تحديد النقطة مباشرة على الخريطة")
            else:
                raise HTTPException(status_code=400, detail="الرجاء تحديد نقطة التسليم الحقيقية على الخريطة أو كتابة العنوان في خانة البحث أولاً")
        else:
            dropoff_address = get_address_from_coords(final_dropoff_lat, final_dropoff_lng)

        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{order.pickup_lng},{order.pickup_lat};{final_dropoff_lng},{final_dropoff_lat}?overview=full&geometries=geojson"
        response = requests.get(osrm_url, timeout=5)
        data = response.json()
        
        if response.status_code != 200 or not data.get("routes"):
            raise HTTPException(status_code=400, detail="تعذر حساب مسار القيادة الحقيقي بين نقطة الاستلام والتسليم، يرجى التأكد من الإحداثيات الصحيحة")
            
        distance_meters = data['routes'][0]['distance']
        distance_km = round(distance_meters / 1000.0, 2)
        route_geometry = data['routes'][0]['geometry']
        
        if distance_km < 3.0:
            total_price = 20.0
        elif 3.0 <= distance_km <= 9.0:
            total_price = 25.0
        elif 9.0 < distance_km <= 12.0:
            total_price = 30.0
        else:
            total_price = 30.0 + ((distance_km - 12.0) * 3.5)
            
        total_price = round(total_price, 2)
        
        order_data = {
            "customer_id": order.user_id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "recipient_phone": order.recipient_phone,
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
            "message": "تم اعتماد وتخزين إحداثيات GPS الحقيقية داخل الدار البيضاء الكبرى بنجاح",
            "data": {
                "distance_km": distance_km,
                "price_mad": total_price,
                "pickup_address": pickup_address,
                "dropoff_address": dropoff_address,
                "route_path": route_geometry,
                "order_details": db_response.data
            }
        }
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
            "message": "تم قبول الطلب بنجاح عبر بايتون",
            "data": db_response.data
        }
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
            "message": "تم تحديث موقع الموصل الحقيقي عبر بايتون بنجاح",
            "data": db_response.data
        }
    except Exception as e:
        print("CRITICAL ERROR IN UPDATE DRIVER LOCATION:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
