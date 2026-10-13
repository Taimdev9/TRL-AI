"""
TRL-AI Backend
FastAPI server يشغّل الموديل ويستقبل الأسئلة من الواجهة
"""

import json
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ===== إعدادات =====
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
MEMORY_FILE = "memory.json"

# متغيرات عامة
model = None
tokenizer = None


# ===== تحميل الموديل عند بداية السيرفر =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    print("⏳ جاري تحميل الموديل...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print("✅ تم تحميل الموديل بنجاح!")
    yield
    print("👋 إغلاق السيرفر")


app = FastAPI(lifespan=lifespan)

# ===== CORS (عشان الواجهة تقدر تتصل) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== نماذج البيانات =====
class ChatRequest(BaseModel):
    message: str

class RateRequest(BaseModel):
    interaction_id: int
    rating: int

class CorrectRequest(BaseModel):
    interaction_id: int
    correction: str


# ===== نظام الذاكرة =====
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def add_interaction(question, answer):
    memory = load_memory()
    interaction = {
        "id": len(memory) + 1,
        "question": question,
        "answer": answer,
        "rating": None,
        "correction": None,
        "timestamp": datetime.now().isoformat()
    }
    memory.append(interaction)
    save_memory(memory)
    return interaction["id"]


# ===== توليد الرد =====
def generate_reply(question):
    messages = [
        {"role": "system", "content": "أنت مساعد ذكي ترد بالعربية بشكل مختصر ومفيد."},
        {"role": "user", "content": question}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )
    return response.strip()


# ===== المسارات (Endpoints) =====
@app.get("/")
def root():
    return {"status": "TRL-AI Backend يعمل ✅"}


@app.post("/chat")
def chat(req: ChatRequest):
    """يستقبل سؤال، يرجّع رد، ويخزّن في الذاكرة"""
    try:
        reply = generate_reply(req.message)
        interaction_id = add_interaction(req.message, reply)
        return {
            "reply": reply,
            "interaction_id": interaction_id
        }
    except Exception as e:
        return {"reply": f"⚠️ خطأ: {str(e)}", "interaction_id": -1}


@app.post("/rate")
def rate(req: RateRequest):
    """يحفظ تقييم المستخدم (1 = 👍, -1 = 👎)"""
    memory = load_memory()
    for item in memory:
        if item["id"] == req.interaction_id:
            item["rating"] = req.rating
            save_memory(memory)
            return {"status": "ok"}
    return {"status": "not_found"}


@app.post("/correct")
def correct(req: CorrectRequest):
    """يحفظ تصحيح المستخدم"""
    memory = load_memory()
    for item in memory:
        if item["id"] == req.interaction_id:
            item["correction"] = req.correction
            save_memory(memory)
            return {"status": "ok"}
    return {"status": "not_found"}


@app.get("/memory")
def get_memory():
    """يرجّع كل الذاكرة"""
    return load_memory()


@app.get("/stats")
def stats():
    """إحصائيات"""
    memory = load_memory()
    rated = [m for m in memory if m["rating"] is not None]
    corrected = [m for m in memory if m["correction"] is not None]
    return {
        "total": len(memory),
        "rated": len(rated),
        "corrected": len(corrected),
        "likes": len([m for m in memory if m["rating"] == 1]),
        "dislikes": len([m for m in memory if m["rating"] == -1])
    } 