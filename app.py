from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pdfminer.high_level import extract_text
import os

app = FastAPI(title="Contract Fee API")

# 掛載 static 資料夾
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ========= PDF 上傳 & 解析 =========
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        text = extract_text(file_path)

        return JSONResponse({"status": "ok", "filename": file.filename, "content": text[:500]})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


# ========= 計算違約金 =========
@app.post("/calculate_penalty")
async def calculate_penalty(
    start_date: str = Form(...),
    end_date: str = Form(...),
    billing_cycle: int = Form(...),
    new_rent: float = Form(...),
    old_rent: float = Form(...),
    package_name: str = Form(...)
):
    try:
        # 簡單違約金計算邏輯 (示範用)
        penalty = (new_rent - old_rent) * billing_cycle

        return JSONResponse({
            "status": "ok",
            "start_date": start_date,
            "end_date": end_date,
            "billing_cycle": billing_cycle,
            "new_rent": new_rent,
            "old_rent": old_rent,
            "package_name": package_name,
            "penalty": penalty
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

# ✅ 啟動入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


