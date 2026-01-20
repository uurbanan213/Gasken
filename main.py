from fastapi import FastAPI, HTTPException, Query
import httpx
import requests
import shapi
from typing import Optional
import time
import json
from datetime import datetime

app = FastAPI()

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
    elif card_number.startswith("35"):
        return "JCB"
    elif card_number.startswith("30") or card_number.startswith("36") or card_number.startswith("38"):
        return "Diners Club"
    else:
        return "Unknown"

def check_expiry(month: str, year: str) -> bool:
    """Cek apakah tanggal kadaluarsa valid"""
    try:
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

def luhn_check(card_number: str) -> bool:
    """Validasi nomor kartu menggunakan algoritma Luhn"""
    try:
        digits = [int(d) for d in str(card_number)]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)
        for digit in even_digits:
            total += sum([int(d) for d in str(digit * 2)])
        return total % 10 == 0
    except:
        return False

@app.get("/")
def read_root():
    return {
        "message": "API is running!",
        "endpoints": ["/", "/health", "/api/check"],
        "usage": "/api/check?cc=5196032181481876|09|28|639&site=https://example.com"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/check")
async def check_cc(
    cc: str = Query(..., description="Card details in format: number|mm|yy|cvv"),
    site: str = Query(..., description="Site URL to check")
):
    """
    Endpoint untuk mengecek kartu kredit
    Format cc: 5196032181481876|09|28|639
    """
    try:
        # Parsing data kartu
        card_parts = cc.split("|")
        if len(card_parts) != 4:
            raise HTTPException(status_code=400, detail="Invalid card format. Use: number|mm|yy|cvv")
        
        card_number = card_parts[0].strip()
        expiry_month = card_parts[1].strip()
        expiry_year = card_parts[2].strip()
        cvv = card_parts[3].strip()
        
        # Validasi dasar
        if not card_number.isdigit() or len(card_number) < 15 or len(card_number) > 19:
            raise HTTPException(status_code=400, detail="Invalid card number")
        
        if not expiry_month.isdigit() or not expiry_year.isdigit():
            raise HTTPException(status_code=400, detail="Invalid expiry date")
        
        if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            raise HTTPException(status_code=400, detail="Invalid CVV")
        
        # Gunakan fungsi dari shapi.py jika ada
        shapi_results = {}
        
        # Coba eksekusi fungsi-fungsi dari shapi.py yang mungkin relevan
        for func_name in ['Wfti0hdS', 'tW3fO9Lj', 'vkvLvJLu', 'tzwAJkb3', 'Ab7vc24Y']:
            if hasattr(shapi, func_name):
                try:
                    func = getattr(shapi, func_name)
                    if callable(func):
                        shapi_results[func_name] = func()
                except:
                    shapi_results[func_name] = "Execution failed"
        
        # Logika pengecekan kartu
        card_type = identify_card_type(card_number)
        is_luhn_valid = luhn_check(card_number)
        is_expiry_valid = check_expiry(expiry_month, expiry_year)
        
        # Cek site
        site_status = "Not checked"
        site_headers = {}
        
        try:
            # Gunakan httpx untuk async request
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
                response = await client.get(site, headers=headers)
                site_status = response.status_code
                if response.headers:
                    site_headers = dict(response.headers)
        except httpx.TimeoutException:
            site_status = "Timeout"
        except httpx.RequestError as e:
            site_status = f"Request error: {str(e)}"
        except Exception as e:
            site_status = f"Error: {str(e)}"
        
        # Buat response
        response_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "request": {
                "card_masked": f"{card_number[:6]}******{card_number[-4:]}",
                "card_length": len(card_number),
                "expiry": f"{expiry_month}/{expiry_year}",
                "cvv_length": len(cvv),
                "site": site
            },
            "validation": {
                "card_type": card_type,
                "luhn_check": is_luhn_valid,
                "expiry_valid": is_expiry_valid,
                "format_valid": True,
                "overall_valid": is_luhn_valid and is_expiry_valid
            },
            "site_check": {
                "status": site_status,
                "headers_count": len(site_headers)
            },
            "shapi": {
                "functions_executed": len(shapi_results),
                "results": shapi_results
            },
            "metadata": {
                "api_version": "1.0",
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        return response_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/shapi/test")
def test_shapi_functions():
    """Test semua fungsi dalam shapi.py"""
    results = {}
    classes = []
    functions = []
    variables = []
    
    for attr_name in dir(shapi):
        if not attr_name.startswith("_"):
            attr = getattr(shapi, attr_name)
            
            if callable(attr):
                # Ini fungsi
                functions.append(attr_name)
                try:
                    results[attr_name] = attr()
                except Exception as e:
                    results[attr_name] = f"Error: {str(e)}"
            elif isinstance(attr, str) and len(attr) > 10:
                # Ini variable string
                variables.append(attr_name)
                results[attr_name] = attr[:50] + "..." if len(attr) > 50 else attr
            elif hasattr(attr, '__class__'):
                # Ini class
                classes.append(attr_name)
                results[attr_name] = f"Class: {attr.__class__.__name__}"
    
    return {
        "summary": {
            "total_classes": len(classes),
            "total_functions": len(functions),
            "total_variables": len(variables),
            "total_items": len(classes) + len(functions) + len(variables)
        },
        "classes": classes,
        "functions": functions,
        "variables": variables,
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
