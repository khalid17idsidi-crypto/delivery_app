from fastapi import APIRouter, HTTPException
import httpx
import requests
from database import supabase
from models import OrderRequest, AcceptOrderRequest, DriverLocationUpdate, RouteRequest
from services import get_address_from_coords, get_coords_from_address

router = APIRouter(tags=["Orders"])

@app_route := router.post("/api/get-live-route")
async def get_live_route(data: RouteRequest):
    url = f"http://router.project-osrm.org/route/v1/driving/{data.start_lng},{data.start_lat};{data.end_lng},{data.end_lat}?overview=full&geometries=geojson"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="فشل في حساب المسار الجغرافي")
            route_data = response.json()
            if not route_data.get("routes"):
                raise HTTPException(status_code=404, detail="لا يوجد مسار متاح")
            return {
                "status": "success",
                "distance_km": round(route_data["routes"][0]["distance"] / 1000.0, 2),
                "duration_mins": round(route_data["routes"][0]["duration"] / 60.0, 1),
                "route_geometry": route_data["routes"][0]["geometry"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-order")
def create_order(order: OrderRequest):
    if not order.security_accepted:
        raise HTTPException(status_code=400, detail="الموافقة على الشروط الأمنية إلزامية")
    if not order.recipient_phone or not order.recipient_phone_secondary:
        raise HTTPException(status_code=400, detail="رقما الهاتف إلزاميان")
    
    pickup_address = get_address_from_coords(order.pickup_lat, order.pickup_lng)
    final_lat = order.dropoff_lat or order.pickup_lat
    final_lng = order.dropoff_lng or order.pickup_lng
    dropoff_address = get_address_from_coords(final_lat, final_lng)
    
    distance_km = 3.0
    price_mad = 25.0

    order_dict = {
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
        "dropoff_lat": final_lat,
        "dropoff_lng": final_lng,
        "distance_km": distance_km,
        "price_mad": price_mad,
        "status": "pending"
    }
    res = supabase.table("orders").insert(order_dict).execute()
    return {"status": "success", "data": res.data}

@router.post("/accept-order")
def accept_order(data: AcceptOrderRequest):
    driver_id = data.driver_id or data.courier_id
    if not driver_id:
        raise HTTPException(status_code=400, detail="معرف الموصل مفقود")
    res = supabase.table("orders").update({"status": "assigned", "driver_id": driver_id}).eq("id", data.order_id).execute()
    return {"status": "success", "data": res.data}

@router.post("/update-driver-location")
def update_driver_location(data: DriverLocationUpdate):
    res = supabase.table("orders").update({"driver_lat": data.lat, "driver_lng": data.lng}).eq("id", data.order_id).execute()
    return {"status": "success", "data": res.data}
