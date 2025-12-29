import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form
import easyocr
import io
from PIL import Image
import re

app = FastAPI()

# تحميل نموذج القراءة (يدعم الإنجليزية)
reader = easyocr.Reader(['en'], gpu=False)

def clean_and_format_plate(raw_text):
    # 1. تنظيف النص من الرموز والمسافات وتحويله للحروف الكبيرة
    clean_text = "".join(e for e in raw_text if e.isalnum()).upper()
    
    # 2. البحث عن أول حرف إنجليزي (A-Z) لتجاهل رقم المحافظة 22
    match = re.search(r'[A-Z]', clean_text)
    
    if match:
        # البدء من موقع الحرف إلى نهاية النص (مثل A12345)
        start_pos = match.start()
        formatted_text = clean_text[start_pos:]
        return formatted_text
    
    return clean_text

@app.post("/scan-and-check")
async def scan_and_check(car_id: str = Form(...), photo: UploadFile = File(...)):
    try:
        # قراءة الصورة المستلمة
        contents = await photo.read()
        image = Image.open(io.BytesIO(contents))
        img_np = np.array(image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # تحسين الصورة (رمادي + تنعيم) لزيادة الدقة
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # تنفيذ القراءة بالذكاء الاصطناعي
        results = reader.readtext(gray)
        
        full_text = ""
        for (bbox, text, prob) in results:
            full_text += text

        # تطبيق منطق القص (تجاهل 22 والتركيز على الحرف وما يليه)
        final_plate = clean_and_format_plate(full_text)

        # قاعدة بيانات وهمية للغرامات (يمكنك ربطها بجدول حقيقي لاحقاً)
        fines_db = {
            "A12345": 50000,
            "B67890": 100000,
            "H55443": 25000
        }

        fine_amount = fines_db.get(final_plate, 0)

        print(f"Original Text: {full_text}")
        print(f"Processed Plate: {final_plate}")

        return {
            "plate": final_plate,
            "total_fines": fine_amount,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)