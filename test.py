import requests

url = "http://127.0.0.1:8000/create-order"
data = {
    "pickup_lat": 33.5731,
    "pickup_lng": -7.5898,
    "dropoff_lat": 33.5898,
    "dropoff_lng": -7.6114
}

response = requests.post(url, json=data)
print("النتيجة:")
print(response.json())

input("اضغط Enter للإغلاق...")
