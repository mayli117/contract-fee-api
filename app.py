from fastapi import FastAPI, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# 簡單的 in-memory DB
contracts_db = {}

@app.get("/", include_in_schema=False)
def root():
    return {"message": "API is running"}

@app.head("/", include_in_schema=False)
def root_head():
    return Response(status_code=200)

def parse_contract_text(text: str):
    parsed = {}
    if "家庭特選餐" in text:
        parsed["package_name"] = "家庭特選餐"
        parsed["contract_days"] = 730
        parsed["cancel_fee_total"] = 3792
    elif "學生優惠餐" in text:
        parsed["package_name"] = "學生優惠餐"
        parsed["contract_days"] = 365
        parsed["cancel_fee_total"] = 2000
    return parsed

@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    text = (await file.read()).decode('utf-8', errors='ignore')
    parsed = parse_contract_text(text)
    if not parsed:
        return JSONResponse(content={"error": "無法識別的合約"}, status_code=400)
    contracts_db[parsed["package_name"]] = {
        "contract_days": parsed["contract_days"],
        "cancel_fee_total": parsed["cancel_fee_total"],
    }
    return JSONResponse(content=parsed)

@app.post("/calculate_fees")
async def calculate_fees(
    start_date: str = Form(...),
    end_date: str = Form(...),
    cycle: int = Form(...),
    new_rent: float = Form(...),
    old_rent: float = Form(...),
    package_name: str = Form(...)
):
    try:
        if package_name not in contracts_db:
            return JSONResponse(
                content={"error": f"找不到套餐 {package_name}，請先上傳合約"},
                status_code=400,
            )
        contract_info = contracts_db[package_name]
        contract_days = contract_info["contract_days"]
        cancel_fee_total = contract_info["cancel_fee_total"]

        fmt = "%Y-%m-%d"
        start = datetime.strptime(start_date, fmt)
        end = datetime.strptime(end_date, fmt)
        if end < start:
            return JSONResponse(content={"error": "end_date must be after start_date"}, status_code=400)
        usage_days = (end - start).days

        cycles = {
            1: (1, 5),
            2: (6, 10),
            3: (11, 15),
            4: (16, 20),
            5: (21, 25),
            6: (26, 30),
        }
        if cycle not in cycles:
            return JSONResponse(content={"error": "Invalid cycle value"}, status_code=400)

        cycle_start, cycle_end = cycles[cycle]

        monthly_diff = new_rent - old_rent
        daily_diff = monthly_diff / 30
        amount = round(daily_diff * usage_days)

        cancel_fee = round(cancel_fee_total / contract_days * usage_days * (contract_days - usage_days) / contract_days)

        result = {
            "package_name": package_name,
            "monthly_rent_diff": monthly_diff,
            "billing_cycle_start": cycle_start,
            "billing_cycle_end": cycle_end,
            "usage_days": usage_days,
            "channel_cancel_fee": cancel_fee,
            "total_fee": amount + cancel_fee
        }
        return JSONResponse(content=result)

    except ValueError:
        return JSONResponse(content={"error": "Invalid date format, use YYYY-MM-DD"}, status_code=400)


# ✅ 啟動入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
