from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pdfminer.high_level import extract_text
import re
import os
from datetime import datetime

app = FastAPI(title="Contract Fee API")

# 掛載靜態檔案 (前端頁面)
if not os.path.exists("static"):
    os.mkdir("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# 全域存套餐資料
parsed_plans = {}

def parse_contract_text(text: str):
    """
    從 PDF 文字解析套餐名稱與優惠金額
    """
    plans = {}
    matches = re.findall(r"([家庭自選豪華全]+餐(?:\(自選20\)|\(全選\))?)\(([\d,]+)元\)", text)
    for name, amount in matches:
        plans[name] = int(amount.replace(",", ""))
    return plans


@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    global parsed_plans
    try:
        text = extract_text(file.file)
        parsed_plans = parse_contract_text(text)

        if not parsed_plans:
            return JSONResponse({"error": "無法識別的合約"}, status_code=400)

        return {"status": "ok", "plans": parsed_plans}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/calculate_fee")
async def calculate_fee(
    plan_name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    new_rent: int = Form(...),
    old_rent: int = Form(...),
):
    global parsed_plans
    if plan_name not in parsed_plans:
        return JSONResponse({"error": f"找不到套餐 {plan_name}，請先上傳合約"}, status_code=400)

    try:
        # 日期計算
        dt_start = datetime.strptime(start_date, "%Y/%m/%d")
        dt_end = datetime.strptime(end_date, "%Y/%m/%d")
        used_days = (dt_end - dt_start).days

        total_days = 730  # 兩年
        total_discount = parsed_plans[plan_name]

        # 違約金公式
        penalty = total_discount * used_days * (total_days - used_days) / (total_days * total_days)

        return {"plan": plan_name, "used_days": used_days, "penalty": round(penalty, 2)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/plans")
async def get_plans():
    """回傳目前解析到的套餐清單"""
    global parsed_plans
    if not parsed_plans:
        return {"error": "尚未上傳合約"}
    return {"plans": parsed_plans}

# ✅ 啟動入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

