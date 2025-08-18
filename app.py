import os
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

# 盡量不因為沒裝 pdfminer 就壞掉
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except Exception:
    pdf_extract_text = None

app = FastAPI(title="Contract Manager (Guarded Edition)")

# CORS（避免瀏覽器預檢/跨網域問題）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 請求日誌
@app.middleware("http")
async def log_requests(request: Request, call_next):
    resp = await call_next(request)
    print(f"[REQ] {request.method} {request.url.path} -> {resp.status_code}")
    return resp

# 只把靜態檔掛在 /static，避免覆蓋 API 路由
app.mount("/static", StaticFiles(directory="static"), name="static")

# 首頁回傳 index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 健康檢查與路由列表（自我診斷）
@app.get("/health")
async def health():
    return {"ok": True, "pdfminer_available": bool(pdf_extract_text)}

@app.get("/debug/routes")
async def debug_routes():
    info: List[Dict[str, Any]] = []
    for r in app.routes:
        try:
            methods = sorted([m for m in r.methods if m not in ("HEAD", "OPTIONS")])
            info.append({"path": r.path, "methods": methods})
        except Exception:
            pass
    return {"routes": info}

# 若誤用 GET /upload_contract，回友善提示（不再 405）
@app.get("/upload_contract")
async def upload_contract_get_hint():
    return JSONResponse(
        {
            "error": "Use POST /upload_contract with multipart/form-data.",
            "example": "curl -X POST http://127.0.0.1:8000/upload_contract -F file=@/path/file.pdf",
        },
        status_code=200,
    )

# 真的上傳解析
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        filename = file.filename or "upload.bin"
        raw = await file.read()
        saved = os.path.join(UPLOAD_DIR, filename)
        with open(saved, "wb") as f:
            f.write(raw)

        # 預設純文字解碼；PDF 則盡量用 pdfminer
        parser = "bytes->utf8"
        preview = raw.decode("utf-8", errors="ignore")

        if filename.lower().endswith(".pdf"):
            if pdf_extract_text:
                preview = pdf_extract_text(saved) or ""
                parser = "pdfminer"
            else:
                # 未安裝 pdfminer，仍降級顯示（非掃描 PDF 通常可看到少量字）
                parser = "fallback-utf8 (no pdfminer.six)"

        return JSONResponse(
            {
                "status": "ok",
                "filename": filename,
                "parser": parser,
                "content_preview": (preview or "")[:1000],  # 最多 1000 字
            }
        )
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

# 違約金計算（示例公式，可依實際規則調整）
@app.post("/calculate_penalty")
async def calculate_penalty(
    start_date: str = Form(...),   # YYYY-MM-DD
    end_date: str = Form(...),     # YYYY-MM-DD
    cycle: int = Form(...),        # 1~6
    new_rent: float = Form(...),
    old_rent: float = Form(...),
    plan_name: str = Form(...),
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if end <= start:
            return JSONResponse({"status": "error", "message": "結束日期需晚於開始日期"}, status_code=400)

        days = (end - start).days
        months = days / 30.0

        # 週期對應違約比例（示例）
        rates = {1: 0.50, 2: 0.40, 3: 0.30, 4: 0.20, 5: 0.10, 6: 0.05}
        rate = rates.get(cycle, 0.05)

        rent_diff = new_rent - old_rent
        base = rent_diff * months
        penalty = max(0.0, base * rate)

        return JSONResponse(
            {
                "status": "ok",
                "plan_name": plan_name,
                "days": days,
                "approx_months": round(months, 4),
                "rent_diff": rent_diff,
                "penalty_rate": rate,
                "formula": f"max(0, (new_rent-old_rent) * (days/30) * rate)",
                "penalty": round(penalty, 2),
            }
        )
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
