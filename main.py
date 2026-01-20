from fastapi import FastAPI, HTTPException, Query
import httpx
import requests
import shapi
from typing import Optional
import time
import json

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "API is running!",
        "endpoints": ["/", "/health", "/api/check"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/check")
async def check_cc(
    cc: str = Query(..., description="Card details in format: number|mm|yy|cvv"),
    site: str = Query(..., description="Shopify site URL")
):
    """
    Endpoint untuk mengecek kartu kredit
    Format cc: 5196032181481876|09|28|639
    """
    try:
        # Parsing data kartu
        card_parts = cc.split("|")
        if len(card_parts) != 4:
            raise HTTPException(status_code=400, detail="Invalid card format")
        
        card_number = card_parts[0]
        expiry_month = card_parts[1]
        expiry_year = card_parts[2]
        cvv = card_parts[3]
        
        # Validasi dasar
        if not card_number.isdigit() or len(card_number) < 15:
            raise HTTPException(status_code=400, detail="Invalid card number")
        
        # Gunakan fungsi dari shapi.py (contoh)
        # Anda bisa memanggil fungsi dari shapi.py sesuai kebutuhan
        example_function_result = ""
        if hasattr(shapi, 'Wfti0hdS'):
            example_function_result = shapi.Wfti0hdS()
        
        # Logika pengecekan (contoh)
        # Anda bisa menambahkan logika pengecekan kartu di sini
        # Misalnya: validasi dengan layanan eksternal
        
        # Contoh: Membuat request ke situs Shopify
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        # Cek apakah situs valid
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(site, headers=headers, follow_redirects=True)
                site_status = response.status_code
        except Exception as e:
            site_status = f"Error: {str(e)}"
        
        # Simulasi pengecekan kartu
        # Dalam implementasi nyata, ini akan berisi logika pengecekan kartu
        card_check_result = {
            "card_bin": card_number[:6],
            "card_type": self.identify_card_type(card_number),
            "is_valid_format": True,
            "expiry_valid": self.check_expiry(expiry_month, expiry_year),
            "site_status": site_status,
            "timestamp": time.time()
        }
        
        # Return response
        return {
            "success": True,
            "message": "Card check completed",
            "data": {
                "card": {
                    "number": f"{card_number[:6]}******{card_number[-4:]}",
                    "expiry": f"{expiry_month}/{expiry_year}",
                    "cvv": "***"
                },
                "site": site,
                "check_result": card_check_result,
                "shapi_function_result": example_function_result
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def identify_card_type(card_number: str) -> str:
    """Identifikasi tipe kartu berdasarkan BIN"""
    if card_number.startswith("4"):
        return "VISA"
    elif card_number.startswith("5"):
        return "MasterCard"
    elif card_number.startswith("34") or card_number.startswith("37"):
        return "American Express"
    elif card_number.startswith("6"):
        return "Discover"
    else:
        return "Unknown"

def check_expiry(month: str, year: str) -> bool:
    """Cek apakah tanggal kadaluarsa valid"""
    try:
        from datetime import datetime
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        
        exp_year = int(year)
        exp_month = int(month)
        
        if exp_year > current_year:
            return True
        elif exp_year == current_year and exp_month >= current_month:
            return True
        return False
    except:
        return False

# Jika Anda ingin menggunakan fungsi-fungsi lain dari shapi.py,
# Anda bisa menambahkan endpoint tambahan sesuai kebutuhan

# Contoh endpoint untuk menjalankan semua fungsi dari shapi.py
@app.get("/api/shapi/functions")
def run_shapi_functions():
    """Menjalankan semua fungsi yang ada di shapi.py"""
    results = {}
    
    # Cari semua fungsi di shapi.py
    for attr_name in dir(shapi):
        attr = getattr(shapi, attr_name)
        if callable(attr) and not attr_name.startswith("_"):
            try:
                results[attr_name] = attr()
            except Exception as e:
                results[attr_name] = f"Error: {str(e)}"
    
    return {
        "success": True,
        "total_functions": len(results),
        "results": results
    }

# Untuk menjalankan server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
