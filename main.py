from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from supabase import create_client, Client

app = FastAPI(title="Delivery Pricing API")

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
    dropoff_lat: float = None
    dropoff_lng: float = None
    dropoff_address_text: str = "" # استقبال العنوان النصي مباشرة من الزبون لتوليد الإحداثيات عند الحاجة
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

# نموذج البيانات القادمة لتحديث الموقع الحي للموصل
class DriverLocationUpdate(BaseModel):
    order_id: str
    driver_id: str
    lat: float
    lng: float

def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except:
        return f"{lat}, {lng}"

# دالة تحويل العنوان النصي إلى إحداثيات (Lat, Lng) في السيرفر تلقائياً
def get_coords_from_address(address_text):
    try:
        query = address_text if "الدار البيضاء" in address_text else f"{address_text}، الدار البيضاء، المغرب"
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        if res and len(res) > 0:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception as e:
        print("Geocoding error in backend:", e)
    return None, None

@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        pickup_address = get_address_from_coords(order.pickup_lat, order.pickup_lng)
        
        # معالجة وتحديد إحداثيات الوصول بدقة (سواء من الدبوس أو استخراجها من النص المكتوب)
        final_dropoff_lat = order.dropoff_lat
        final_dropoff_lng = order.dropoff_lng
        dropoff_address = ""

        if (not final_dropoff_lat or not final_dropoff_lng) and order.dropoff_address_text:
            lat, lng = get_coords_from_address(order.dropoff_address_text)
            if lat and lng:
                final_dropoff_lat = lat
                final_dropoff_lng = lng
                dropoff_address = order.dropoff_address_text
            else:
                final_dropoff_lat = 33.5898
                final_dropoff_lng = -7.6114
                dropoff_address = order.dropoff_address_text
        elif final_dropoff_lat and final_dropoff_lng:
            dropoff_address = get_address_from_coords(final_dropoff_lat, final_dropoff_lng)
        else:
            final_dropoff_lat = 33.5898
            final_dropoff_lng = -7.6114
            dropoff_address = "الدار البيضاء"

        # طلب المسار الفعلي الدقيق (GeoJSON LineString) من خدمة OSRM لرسم خط السير على الخريطة
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{order.pickup_lng},{order.pickup_lat};{final_dropoff_lng},{final_dropoff_lat}?overview=full&geometries=geojson"
        response = requests.get(osrm_url, timeout=5)
        data = response.json()
        
        route_geometry = None
        if response.status_code == 200 and data.get("routes"):
            distance_meters = data['routes'][0]['distance']
            distance_km = round(distance_meters / 1000.0, 2)
            route_geometry = data['routes'][0]['geometry']
        else:
            distance_km = 2.0
            route_geometry = {
                "type": "LineString",
                "coordinates": [
                    [order.pickup_lng, order.pickup_lat],
                    [final_dropoff_lng, final_dropoff_lat]
                ]
            }
        
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
            "route_path": route_geometry  # تخزين مسار الرحلة في قاعدة البيانات
        }
        
        db_response = supabase.table("orders").insert(order_data).execute()
        
        return {
            "status": "success",
            "message": "تم إيجاد المسار وحفظ الطلب بنجاح",
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
            "message": "تم قبول الطلب بنجاح",
            "data": db_response.data
        }
    except Exception as e:
        print("CRITICAL ERROR IN ACCEPT ORDER:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# دالة استقبال وتحديث الموقع الحي للموصل في السيرفر
@app.post("/update-driver-location")
def update_driver_location(data: DriverLocationUpdate):
    try:
        db_response = supabase.table("orders").update({
            "driver_lat": data.lat,
            "driver_lng": data.lng
        }).eq("id", data.order_id).execute()
        
        return {
            "status": "success",
            "message": "تم تحديث موقع الموصل بنجاح عبر السيرفر",
            "data": db_response.data
        }
    except Exception as e:
        print("CRITICAL ERROR IN UPDATE DRIVER LOCATION:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
