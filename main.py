from fastapi import FastAPI, HTTPException, Query
import httpx
import shapi
import time
from datetime import datetime
import asyncio
from typing import Dict, List, Any
import re

app = FastAPI()

# Helper functions
def identify_card_type(card_number: str) -> str:
    """Identifikasi tipe kartu berdasarkan BIN"""
    first_two = card_number[:2]
    first_six = card_number[:6]
    
    # BIN checks
    if card_number.startswith("4"):
        return "VISA"
    elif card_number.startswith(("51", "52", "53", "54", "55")):
        return "MasterCard"
    elif card_number.startswith(("34", "37")):
        return "American Express"
    elif card_number.startswith(("300", "301", "302", "303", "304", "305", "36", "38")):
        return "Diners Club"
    elif card_number.startswith(("6011", "65", "644", "645", "646", "647", "648", "649", "622")):
        return "Discover"
    elif 622126 <= int(first_six) <= 622925:
        return "Discover"
    elif card_number.startswith("35"):
        return "JCB"
    elif card_number.startswith(("50", "56", "57", "58", "63", "67")):
        return "Maestro"
    else:
        return "Unknown"

def check_expiry(month: str, year: str) -> Dict[str, Any]:
    """Cek tanggal kadaluarsa dengan detail"""
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        exp_year = int("20" + year) if len(year) == 2 else int(year)
        exp_month = int(month)
        
        # Validasi bulan
        if exp_month < 1 or exp_month > 12:
            return {"valid": False, "reason": "Invalid month"}
        
        # Cek apakah sudah expired
        if exp_year < current_year:
            return {"valid": False, "reason": "Card expired (year)"}
        elif exp_year == current_year and exp_month < current_month:
            return {"valid": False, "reason": "Card expired (month)"}
        
        # Hitung sisa bulan
        months_remaining = (exp_year - current_year) * 12 + (exp_month - current_month)
        
        return {
            "valid": True,
            "months_remaining": months_remaining,
            "expiry_date": f"{exp_month:02d}/{str(exp_year)[-2:]}"
        }
    except:
        return {"valid": False, "reason": "Invalid date format"}

def luhn_check(card_number: str) -> Dict[str, Any]:
    """Validasi nomor kartu menggunakan algoritma Luhn"""
    try:
        digits = [int(d) for d in str(card_number)]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)
        for digit in even_digits:
            for d in str(digit * 2):
                total += int(d)
        
        is_valid = total % 10 == 0
        
        return {
            "valid": is_valid,
            "check_digit": digits[-1],
            "calculated_check": (10 - (total % 10)) % 10
        }
    except:
        return {"valid": False, "reason": "Calculation error"}

def calculate_score(luhn_result: Dict, expiry_result: Dict) -> float:
    """Calculate validation score (0-100)"""
    score = 0
    
    # Luhn check: 40 points
    if luhn_result.get("valid", False):
        score += 40
    
    # Expiry check: 40 points
    if expiry_result.get("valid", False):
        score += 40
        
        # Bonus for longer validity
        months = expiry_result.get("months_remaining", 0)
        if months > 12:
            score += min(10, months // 12)
    
    # Format check: 20 points (assuming format is correct if we got here)
    score += 20
    
    return min(100, score)

def analyze_shapi_content() -> Dict[str, Any]:
    """Analisis isi shapi.py secara mendalam"""
    analysis = {
        "classes": [],
        "functions": [],
        "variables": [],
        "patterns": [],
        "total_lines": 0
    }
    
    try:
        # Baca file shapi.py
        with open("shapi.py", "r", encoding="utf-8") as f:
            lines = f.readlines()
            analysis["total_lines"] = len(lines)
            
            for line in lines:
                line = line.strip()
                
                # Deteksi class
                if line.startswith("class "):
                    class_name = line.split()[1].split(":")[0]
                    analysis["classes"].append(class_name)
                
                # Deteksi fungsi
                elif line.startswith("def "):
                    func_name = line.split()[1].split("(")[0]
                    analysis["functions"].append(func_name)
                
                # Deteksi variabel
                elif " = '" in line and not line.startswith("#"):
                    var_name = line.split(" = ")[0].strip()
                    if " = '" in line or ' = "' in line:
                        analysis["variables"].append(var_name)
                
                # Deteksi pola khusus
                if "self.x = '" in line:
                    pattern = line.split("self.x = '")[1].split("'")[0]
                    if len(pattern) > 5:
                        analysis["patterns"].append(pattern[:20] + "...")
    
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis

async def execute_all_shapi_functions() -> Dict[str, Any]:
    """Eksekusi SEMUA fungsi dari shapi.py secara parallel"""
    results = {}
    errors = []
    
    # Kumpulkan semua fungsi dari shapi.py
    function_names = []
    for attr_name in dir(shapi):
        if not attr_name.startswith("_"):
            attr = getattr(shapi, attr_name)
            if callable(attr):
                function_names.append(attr_name)
    
    # Eksekusi fungsi secara async
    async def execute_function(func_name):
        try:
            func = getattr(shapi, func_name)
            result = func()
            return func_name, {"success": True, "result": result}
        except Exception as e:
            return func_name, {"success": False, "error": str(e)}
    
    # Jalankan semua fungsi
    tasks = [execute_function(name) for name in function_names]
    completed = await asyncio.gather(*tasks)
    
    for func_name, result in completed:
        results[func_name] = result
        if not result["success"]:
            errors.append(func_name)
    
    return {
        "total_functions": len(function_names),
        "executed": len(results),
        "successful": len(results) - len(errors),
        "failed": len(errors),
        "errors": errors,
        "results": results
    }

@app.get("/")
def read_root():
    return {
        "message": "Shapi CC Check API",
        "version": "2.1",
        "endpoints": {
            "/": "API info",
            "/health": "Health check",
            "/api/check": "Check CC with shapi functions",
            "/api/shapi/analyze": "Analyze shapi.py content",
            "/api/shapi/execute": "Execute ALL shapi functions",
            "/api/validate": "Validate CC only"
        },
        "usage": "GET /api/check?cc=5196032181481876|09|28|639&site=https://example.com"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "shapi_loaded": hasattr(shapi, 'Wfti0hdS')
    }

@app.get("/api/validate")
def validate_cc_only(
    cc: str = Query(..., description="Card: number|mm|yy|cvv")
):
    """Validasi kartu kredit saja (tanpa site check)"""
    try:
        card_parts = cc.split("|")
        if len(card_parts) != 4:
            raise HTTPException(status_code=400, detail="Format: number|mm|yy|cvv")
        
        card_number = card_parts[0].strip()
        expiry_month = card_parts[1].strip()
        expiry_year = card_parts[2].strip()
        cvv = card_parts[3].strip()
        
        # Validasi
        card_type = identify_card_type(card_number)
        luhn_result = luhn_check(card_number)
        expiry_result = check_expiry(expiry_month, expiry_year)
        
        # Eksekusi beberapa fungsi shapi sebagai sample
        shapi_samples = {}
        sample_functions = ['Wfti0hdS', 'tW3fO9Lj', 'vkvLvJLu', 'tzwAJkb3', 'Ab7vc24Y']
        
        for func_name in sample_functions:
            if hasattr(shapi, func_name):
                try:
                    func = getattr(shapi, func_name)
                    shapi_samples[func_name] = func()
                except:
                    shapi_samples[func_name] = None
        
        # Hitung score
        overall_score = calculate_score(luhn_result, expiry_result)
        
        return {
            "success": True,
            "card_info": {
                "type": card_type,
                "bin": card_number[:6],
                "last4": card_number[-4:],
                "length": len(card_number),
                "expiry": expiry_result.get("expiry_date", "invalid"),
                "cvv_length": len(cvv)
            },
            "validation": {
                "luhn_algorithm": luhn_result,
                "expiry_check": expiry_result,
                "overall_score": overall_score,
                "overall_valid": luhn_result.get("valid", False) and expiry_result.get("valid", False)
            },
            "shapi_sample": {
                "functions_tested": len(shapi_samples),
                "results": shapi_samples
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/check")
async def check_cc_comprehensive(
    cc: str = Query(..., description="Card details: number|mm|yy|cvv"),
    site: str = Query(None, description="Site URL to check (optional)"),
    full_shapi: bool = Query(False, description="Execute ALL shapi functions")
):
    """
    Comprehensive CC check with optional site validation
    and shapi function execution
    """
    start_time = time.time()
    
    try:
        # Parse CC
        card_parts = cc.split("|")
        if len(card_parts) != 4:
            raise HTTPException(status_code=400, detail="Format: number|mm|yy|cvv")
        
        card_number = card_parts[0].strip()
        expiry_month = card_parts[1].strip()
        expiry_year = card_parts[2].strip()
        cvv = card_parts[3].strip()
        
        # Basic validation
        if not card_number.isdigit():
            raise HTTPException(status_code=400, detail="Card number must be digits")
        
        # Card analysis
        card_type = identify_card_type(card_number)
        luhn_result = luhn_check(card_number)
        expiry_result = check_expiry(expiry_month, expiry_year)
        
        # Hitung score
        overall_score = calculate_score(luhn_result, expiry_result)
        
        # Site check (if provided)
        site_info = {}
        if site:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "*/*"
                    }
                    response = await client.get(site, headers=headers, follow_redirects=True)
                    site_info = {
                        "status": response.status_code,
                        "url": str(response.url),
                        "content_type": response.headers.get("content-type", ""),
                        "server": response.headers.get("server", ""),
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000)
                    }
            except Exception as e:
                site_info = {"error": str(e), "status": "failed"}
        
        # Shapi functions execution
        shapi_execution = {}
        if full_shapi:
            # Execute ALL functions
            shapi_execution = await execute_all_shapi_functions()
        else:
            # Execute sample functions
            sample_results = {}
            sample_functions = [
                'Wfti0hdS', 'tW3fO9Lj', 'vkvLvJLu', 'tzwAJkb3', 'Ab7vc24Y',
                'AqyX0Hox', 'I4HthtEs', 'ARCmx45o', 'sruPWJbL', 'HBeDrCS1',
                'rbgvAXVA', 'mKQQw65p', 'Dgaln23z', 'keojhaRi', 'EmEWRbYR'
            ]
            
            for func_name in sample_functions:
                if hasattr(shapi, func_name):
                    try:
                        func = getattr(shapi, func_name)
                        sample_results[func_name] = func()
                    except Exception as e:
                        sample_results[func_name] = f"Error: {str(e)}"
            
            shapi_execution = {
                "mode": "sample",
                "functions_executed": len(sample_results),
                "results": sample_results
            }
        
        # Analyze shapi content
        shapi_analysis = analyze_shapi_content()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build response
        response = {
            "success": True,
            "processing_time_ms": round(processing_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
            
            "card": {
                "masked": f"{card_number[:6]}******{card_number[-4:]}",
                "type": card_type,
                "bin": card_number[:6],
                "last4": card_number[-4:],
                "length": len(card_number)
            },
            
            "validation": {
                "luhn_check": luhn_result,
                "expiry_check": expiry_result,
                "cvv_valid": len(cvv) in [3, 4] and cvv.isdigit(),
                "overall_score": overall_score
            },
            
            "site": site_info if site else {"checked": False},
            
            "shapi": {
                "analysis": shapi_analysis,
                "execution": shapi_execution,
                "total_items": len(shapi_analysis.get("classes", [])) + 
                              len(shapi_analysis.get("functions", [])) + 
                              len(shapi_analysis.get("variables", []))
            },
            
            "metadata": {
                "api_version": "2.1",
                "request_id": f"req_{int(time.time())}",
                "note": "Shapi CC Validation API"
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "traceback": traceback.format_exc()[-500:]  # Limit traceback length
            }
        )

@app.get("/api/shapi/analyze")
def analyze_shapi():
    """Deep analysis of shapi.py content"""
    analysis = analyze_shapi_content()
    
    # Additional: Try to detect patterns in variable values
    patterns_detected = []
    for var_name in analysis.get("variables", []):
        try:
            var_value = getattr(shapi, var_name)
            if isinstance(var_value, str) and len(var_value) > 10:
                # Check if it looks like encoded/encrypted data
                if all(c.isalnum() or c in '!@#$%^&*()' for c in var_value):
                    patterns_detected.append({
                        "variable": var_name,
                        "type": "alphanumeric_string",
                        "length": len(var_value),
                        "sample": var_value[:30]
                    })
        except:
            pass
    
    return {
        "file_analysis": analysis,
        "detected_patterns": patterns_detected,
        "summary": {
            "total_classes": len(analysis.get("classes", [])),
            "total_functions": len(analysis.get("functions", [])),
            "total_variables": len(analysis.get("variables", [])),
            "total_lines": analysis.get("total_lines", 0)
        }
    }

@app.get("/api/shapi/execute")
async def execute_shapi_functions():
    """Execute ALL functions from shapi.py"""
    try:
        result = await execute_all_shapi_functions()
        return {
            "success": True,
            "execution_summary": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shapi/classes")
def list_shapi_classes():
    """List all classes in shapi.py and their properties"""
    classes_info = []
    
    for attr_name in dir(shapi):
        if not attr_name.startswith("_"):
            attr = getattr(shapi, attr_name)
            
            # Check if it's a class
            try:
                if isinstance(attr, type):
                    class_info = {
                        "name": attr_name,
                        "module": attr.__module__,
                        "methods": [m for m in dir(attr) if not m.startswith("_")],
                        "has_init": hasattr(attr, "__init__")
                    }
                    
                    # Try to instantiate and get x value
                    try:
                        instance = attr()
                        if hasattr(instance, 'x'):
                            class_info["x_value"] = instance.x
                        class_info["instantiable"] = True
                    except:
                        class_info["instantiable"] = False
                    
                    classes_info.append(class_info)
            except:
                pass
    
    return {
        "total_classes": len(classes_info),
        "classes": classes_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
