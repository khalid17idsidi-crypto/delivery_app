from pydantic import BaseModel
from typing import Optional

class OrderRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    dropoff_address_text: Optional[str] = ""
    user_id: Optional[str] = "user_123"
    customer_name: Optional[str] = "أمين"
    customer_phone: Optional[str] = "0600000000"
    recipient_phone: str
    recipient_phone_secondary: str
    package_type: Optional[str] = "طرد"
    notes: Optional[str] = ""
    security_accepted: bool = False

class AcceptOrderRequest(BaseModel):
    order_id: str
    driver_id: Optional[str] = None
    courier_id: Optional[str] = None

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

class WalletTopupRequest(BaseModel):
    user_id: str
    amount: float
    receipt_url: str = "https://via.placeholder.com/150"
