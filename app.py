from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# 掛載 static 資料夾
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# 📌 合約檔案上傳
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        return JSONResponse({
            "status": "ok",
            "filename": file.filename,
            "preview": text[:200]  # 只顯示前 200 字
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


# 📌 違約金計算
@app.post("/calculate_penalty")
async def calculate_penalty(
    start_date: str = Form(...),
    end_date: str = Form(...),
    cycle: int = Form(...),       # 計費週期（1~6）
    new_rent: float = Form(...),  # 新租金
    old_rent: float = Form(...),  # 舊租金
    plan_name: str = Form(...)    # 套餐名稱
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end - start).days

        # 📌 設定違約比例（依週期不同）
        penalty_rates = {
            1: 0.5,   # 第 1 週期：50%
            2: 0.4,   # 第 2 週期：40%
            3: 0.3,   # 第 3 週期：30%
            4: 0.2,   # 第 4 週期：20%
            5: 0.1,   # 第 5 週期：10%
            6: 0.05   # 第 6 週期：5%
        }
        rate = penalty_rates.get(cycle, 0.05)

        # 📌 計算違約金公式
        rent_diff = new_rent - old_rent
        penalty = rent_diff * (total_days / 30) * rate  # 以月為單位，乘上違約比例

        return JSONResponse({
            "status": "ok",
            "plan_name": plan_name,
            "days": total_days,
            "rent_diff": rent_diff,
            "penalty_rate": rate,
            "penalty": round(penalty, 2)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

