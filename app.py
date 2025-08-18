from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pdfminer.high_level import extract_text
from datetime import datetime

app = FastAPI()

# 前端靜態檔案
app.mount("/", StaticFiles(directory="static", html=True), name="static")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ 上傳合約檔案並解析文字
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 讀取 PDF 文字
        text = extract_text(file_path)

        return JSONResponse({
            "status": "ok",
            "filename": file.filename,
            "content_preview": text[:500]  # 只顯示前 500 字避免太長
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

# ✅ 計算違約金 API
@app.post("/calculate_fee")
async def calculate_fee(
    start_date: str = Form(...),
    end_date: str = Form(...),
    cycle: int = Form(...),
    new_rent: int = Form(...),
    old_rent: int = Form(...),
    plan_name: str = Form(...)
):
    try:
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        days = (d2 - d1).days

        # 簡單的違約金算法：差額 * 週期 * 天數 / 30
        penalty = (new_rent - old_rent) * cycle * (days / 30)

        return JSONResponse({
            "status": "ok",
            "plan_name": plan_name,
            "days": days,
            "penalty": round(penalty, 2)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
