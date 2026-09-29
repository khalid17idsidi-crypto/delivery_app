from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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

SUPABASE_URL = "https://cauujrnxtqswjzanphyq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNDEwNDMsImV4cCI6MjEwMzkxNzA0M30.xIwYyOcOaH-3VEkfuf2T73tHMRn3oAL2_RjNNPueQKU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# نموذج مرن جداً لتقبل الإحداثيات بأي صيغة يرسلها الهاتف
class OrderRequest(BaseModel):
    pickup_lat: float = 33.5731
    pickup_lng: float = -7.5898
    dropoff_lat: float = 33.5900
    dropoff_lng: float = -7.6100
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

def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except:
        return f"{lat}, {lng}"

@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        # التأكد من صحة الإحداثيات واستخدام قيم افتراضية لمدينة الدار البيضاء إذا كانت فارغة
        p_lat = order.pickup_lat if order.pickup_lat != 0 else 33.5731
        p_lng = order.pickup_lng if order.pickup_lng != 0 else -7.5898
        d_lat = order.dropoff_lat if order.dropoff_lat != 0 else 33.5900
        d_lng = order.dropoff_lng if order.dropoff_lng != 0 else -7.6100

        pickup_address = get_address_from_coords(p_lat, p_lng)
        dropoff_address = get_address_from_coords(d_lat, d_lng)
        
        # حساب المسافة الفعلية عبر OSRM
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{p_lng},{p_lat};{d_lng},{d_lat}?overview=false"
        response = requests.get(osrm_url, timeout=3)
        data = response.json()
        
        if response.status_code != 200 or not data.get("routes"):
            distance_km = 3.5  # مسافة افتراضية منطقية في حال انقطاع الخريطة المؤقت
        else:
            distance_meters = data['routes'][0]['distance']
            distance_km = round(distance_meters / 1000.0, 2)
        
        # منطق التسعير الصحيح والدقيق حسب المسافة
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
            "user_id": order.user_id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "recipient_phone": order.recipient_phone,
            "package_type": order.package_type,
            "notes": order.notes,
            "pickup_address": pickup_address,
            "dropoff_address": dropoff_address,
            "pickup_lat": p_lat,
            "pickup_lng": p_lng,
            "dropoff_lat": d_lat,
            "dropoff_lng": d_lng,
            "distance_km": distance_km,
            "price": total_price,
            "price_mad": total_price,
            "status": "pending"
        }
        
        db_response = supabase.table("orders").insert(order_data).execute()
        
        return {
            "status": "success",
            "message": "تم إيجاد المسار وحفظ الطلب بنجاح",
            "data": {
                "distance_km": distance_km,
                "price": total_price,
                "price_mad": total_price,
                "pickup_address": pickup_address,
                "dropoff_address": dropoff_address,
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
            "driver_id": the_driver_id,
            "courier_id": the_driver_id
        }).eq("id", data.order_id).execute()
        
        return {
            "status": "success",
            "message": "تم قبول الطلب بنجاح",
            "data": db_response.data
        }
    except Exception as e:
        print("CRITICAL ERROR IN ACCEPT ORDER:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
