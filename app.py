from fastapi import FastAPI,Response,UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
app = FastAPI()
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
       parsed["channel_cancel_fee_total"] = 3792
   return parsed
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
   text = (await file.read()).decode('utf-8', errors='ignore')
   parsed = parse_contract_text(text)
   return JSONResponse(content=parsed)
@app.post("/calculate_fees")
async def calculate_fees(
   start_date: str = Form(...),
   end_date: str = Form(...),
   cycle: int = Form(...),
   new_rent: float = Form(...),
   old_rent: float = Form(...),
   package_name: str = Form(...),
   usage_days: int = Form(...)
):
   cycles = {
       1: (1, 5),
       2: (6, 10),
       3: (11, 20),
       4: (16, 25),
       5: (21, 30),
       6: (26, 35),
   }
   cycle_start, cycle_end = cycles.get(cycle, (1, 5))
   monthly_diff = new_rent - old_rent
   daily_diff = monthly_diff / 30
   amount = round(daily_diff * usage_days)
   contract_days = 730
   cancel_fee_total = 3792
   cancel_fee = round(cancel_fee_total / contract_days * usage_days * (contract_days - usage_days) / contract_days)
   result = {
       "monthly_rent_diff": monthly_diff,
       "billing_cycle_start": cycle_start,
       "billing_cycle_end": cycle_end,
       "usage_days": usage_days,
       "channel_cancel_fee": cancel_fee,
       "total_fee": amount + cancel_fee
   }
   return JSONResponse(content=result)
if __name__ == "__main__":

   uvicorn.run(app, host="0.0.0.0", port=8000)

