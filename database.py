import requests
from supabase import create_client, Client

SUPABASE_URL = "https://cauujrnxtqswjzqhphyq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODM0MTA0MywiZXhwIjoyMTAzOTE3MDQzfQ.17AG1uMHj14ZNVuzp56-9_Z2KYeG50Oo3k__kDbhUok"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
