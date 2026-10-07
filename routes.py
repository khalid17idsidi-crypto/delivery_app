import httpx
import requests
from fastapi import APIRouter, HTTPException
from database import supabase, get_address_from_coords, get_coords_from_address
from models import (
    OrderRequest,
    AcceptOrderRequest,
    DriverLocationUpdate,
    RouteRequest,
    WalletTopupRequest
)

router = APIRouter()

@router.post("/api/get-live-route")
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

@router.post("/create-order")
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

@router.post("/accept-order")
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

@router.post("/update-driver-location")
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

@router.post("/api/wallet/topup")
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