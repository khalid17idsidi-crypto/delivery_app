from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from supabase import create_client, Client

# 1. إعداد تطبيق FastAPI والـ CORS
app = FastAPI(title="Delivery Pricing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. إعداد الاتصال بـ Supabase (القيم الحقيقية)
SUPABASE_URL = "https://cauujrnxtqswjzanphyq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNDEwNDMsImV4cCI6MjEwMzkxNzA0M30.xIwYyOcOaH-3VEkfuf2T73tHMRn3oAL2_RjNNPueQKU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. نموذج البيانات القادمة من الموبايل لإنشاء الطلب
class OrderRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    user_id: str = "user_123"
    customer_name: str = "أمين"
    customer_phone: str = "0600000000"
    recipient_phone: str = "0700000000"
    package_type: str = "طرد"
    notes: str = ""

# نموذج البيانات القادمة لقبول الطلب من الموصل
class AcceptOrderRequest(BaseModel):
    order_id: str
    courier_id: str

# دالة جلب العنوان من Nominatim
def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers).json()
        return res.get('display_name', f"{lat}, {lng}")
    except:
        return f"{lat}, {lng}"

# 4. الـ Endpoint لإنشاء الطلب
@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        # جلب العناوين
        pickup_address = get_address_from_coords(order.pickup_lat, order.pickup_lng)
        dropoff_address = get_address_from_coords(order.dropoff_lat, order.dropoff_lng)
        
        # حساب المسافة بـ OSRM
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{order.pickup_lng},{order.pickup_lat};{order.dropoff_lng},{order.dropoff_lat}?overview=false"
        response = requests.get(osrm_url, timeout=5)
        data = response.json()
        
        if response.status_code != 200 or not data.get("routes"):
            raise HTTPException(status_code=400, detail="فشل في حساب المسافة عبر الخرائط")
        
        distance_meters = data['routes'][0]['distance']
        distance_km = round(distance_meters / 1000.0, 2)
        
        # منطق التسعير
        if distance_km < 3.0:
            total_price = 20.0
        elif 3.0 <= distance_km <= 9.0:
            total_price = 25.0
        elif 9.0 < distance_km <= 12.0:
            total_price = 30.0
        else:
            total_price = 30.0 + ((distance_km - 12.0) * 3.5)
            
        total_price = round(total_price, 2)
        
        # تجهيز البيانات والحفظ في Supabase
        order_data = {
            "user_id": order.user_id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "recipient_phone": order.recipient_phone,
            "package_type": order.package_type,
            "notes": order.notes,
            "pickup_address": pickup_address,
            "dropoff_address": dropoff_address,
            "pickup_lat": order.pickup_lat,
            "pickup_lng": order.pickup_lng,
            "dropoff_lat": order.dropoff_lat,
            "dropoff_lng": order.dropoff_lng,
            "distance_km": distance_km,
            "price_mad": total_price,
            "status": "pending"
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
                "order_details": db_response.data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. الـ Endpoint الجديد لقبول الطلب من طرف الموصل
@app.post("/accept-order")
def accept_order(data: AcceptOrderRequest):
    try:
        # تحديث حالة الطلب في جدول orders في قاعدة بيانات Supabase
        db_response = supabase.table("orders").update({
            "status": "accepted",
            "courier_id": data.courier_id
        }).eq("id", data.order_id).execute()
        
        return {
            "status": "success",
            "message": "تم قبول الطلب بنجاح",
            "data": db_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
