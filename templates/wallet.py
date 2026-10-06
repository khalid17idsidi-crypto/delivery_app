from fastapi import APIRouter, HTTPException
from database import supabase
from models import WalletTopupRequest

router = APIRouter(tags=["Wallet"])

@router.post("/api/wallet/topup")
async def wallet_topup(data: WalletTopupRequest):
    try:
        if data.amount < 30:
            raise HTTPException(status_code=400, detail="الحد الأدنى للشحن هو 30 درهم")
        
        bonus = 10.0 if data.amount >= 100 else (4.0 if data.amount >= 50 else 0.0)
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
        return {
            "status": "success", 
            "message": "تم إرسال طلب الشحن بنجاح في انتظار مراجعة الأدمن", 
            "data": db_res.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))