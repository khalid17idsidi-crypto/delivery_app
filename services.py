import requests

def get_address_from_coords(lat: float, lng: float) -> str:
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        return res.get('display_name', f"{lat}, {lng}")
    except Exception:
        return f"{lat}, {lng}"

def get_coords_from_address(address_text: str):
    try:
        query = address_text if "الدار البيضاء" in address_text else f"{address_text}, الدار البيضاء, المغرب"
        url = "https://nominatim.openstreetmap.org/search?q=" + requests.utils.quote(query) + "&format=json&limit=1"
        headers = {'User-Agent': 'DeliveryApp/1.0'}
        res = requests.get(url, headers=headers, timeout=3).json()
        if res and len(res) > 0:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception as e:
        print("Geocoding error:", e)
    return None, None