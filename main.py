@app.post("/create-order")
def create_order(order: OrderRequest):
    try:
        # التحقق من إحداثيات الاستلام
        if not order.pickup_lat or not order.pickup_lng:
            raise HTTPException(status_code=400, detail="موقع الاستلام عبر GPS غير متوفر")
            
        pickup_address = get_address_from_coords(order.pickup_lat, order.pickup_lng)
        
        final_dropoff_lat = order.dropoff_lat
        final_dropoff_lng = order.dropoff_lng
        dropoff_address = ""

        # التحقق من إحداثيات التسليم (إما عبر الخريطة أو عبر النص)
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

        # حساب المسافة الحقيقية عبر OSRM
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
            "route_path": route_geometry
        }
        
        db_response = supabase.table("orders").insert(order_data).execute()
        
        return {
            "status": "success",
            "message": "تم حساب المسار الحقيقي وتخزين الطلب بنجاح عبر بايتون",
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
