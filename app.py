from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pdfminer.high_level import extract_text
from datetime import datetime

app = FastAPI()

# 提供 index.html
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# 上傳合約檔案
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        text = extract_text(file.file)   # 讀 PDF 文字
        return JSONResponse({
            "status": "ok",
            "message": "檔案上傳成功",
            "preview": text[:300]  # 預覽前 300 字
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


# 計算違約金
@app.post("/calculate_fee")
async def calculate_fee(
    start_date: str = Form(...),
    end_date: str = Form(...),
    period: int = Form(...),
    new_rent: int = Form(...),
    old_rent: int = Form(...),
    plan_name: str = Form(...)
):
    try:
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        days = (d2 - d1).days
        weeks = days // 7

        # 簡單違約金公式
        penalty = (old_rent - new_rent) * weeks * period
        if penalty < 0:
            penalty = 0

        return JSONResponse({
            "status": "ok",
            "plan": plan_name,
            "weeks": weeks,
            "penalty": penalty
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

# ✅ 啟動入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



