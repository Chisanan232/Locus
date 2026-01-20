from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, AsyncGenerator
import asyncio
import json
from sqlmodel import SQLModel, Field as SQLField  # 預留 SQLModel

app = FastAPI()

# 設定 CORS 允許前端存取
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Data Models (Pydantic & SQLModel 混合設計) ---

class Location(BaseModel):
    name: str
    lat: float
    lng: float
    description: str


class DayPlan(BaseModel):
    day: int
    locations: List[Location]
    summary: str


class ItineraryResponse(BaseModel):
    trip_name: str
    days: List[DayPlan]


# --- Mock Data & Logic ---
# 在真實場景中，這裡會是 Pydantic AI 的 Agent.run_stream()
# 為了讓你立刻看到 "地球縮放" 和 "打點" 效果，我們模擬一個 AI 逐步生成的過程

MOCK_TOKYO_TRIP = [
    {
        "day": 1,
        "summary": "抵達東京，探索淺草文化",
        "locations": [
            {"name": "成田機場", "lat": 35.7719, "lng": 140.3929, "description": "抵達日本"},
            {"name": "淺草寺", "lat": 35.7147, "lng": 139.7967, "description": "東京最古老的寺廟，雷門打卡"},
            {"name": "晴空塔", "lat": 35.7100, "lng": 139.8107, "description": "俯瞰東京夜景"}
        ]
    },
    {
        "day": 2,
        "summary": "潮流與購物的一天",
        "locations": [
            {"name": "澀谷十字路口", "lat": 35.6594, "lng": 139.7005, "description": "世界上最繁忙的十字路口"},
            {"name": "明治神宮", "lat": 35.6763, "lng": 139.6993, "description": "市中心的森林綠洲"},
            {"name": "新宿御苑", "lat": 35.6851, "lng": 139.7100, "description": "著名的賞櫻勝地"}
        ]
    }
]


async def ai_stream_generator(prompt: str) -> AsyncGenerator[str, None]:
    """
    模擬 AI 思考並一段一段吐出資料的過程 (Server-Sent Events 格式)
    """
    # 1. 模擬思考
    yield json.dumps({"type": "status", "content": "正在分析您的旅遊需求..."}) + "\n"
    await asyncio.sleep(1)

    yield json.dumps({"type": "status", "content": "正在搜尋東京熱門景點..."}) + "\n"
    await asyncio.sleep(1)

    # 2. 開始規劃行程 (移動地圖視角)
    # 告訴前端先飛到東京
    yield json.dumps({
        "type": "control",
        "action": "fly_to",
        "data": {"lat": 35.6895, "lng": 139.6917, "zoom": 10}
    }) + "\n"
    await asyncio.sleep(1.5)

    # 3. 逐天生成景點 (前端收到後會打點、連線)
    for day_plan in MOCK_TOKYO_TRIP:
        yield json.dumps({"type": "status", "content": f"正在規劃第 {day_plan['day']} 天：{day_plan['summary']}"}) + "\n"

        # 這裡我們模擬 AI "一個景點一個景點" 生出來
        current_locations = []
        for loc in day_plan['locations']:
            await asyncio.sleep(0.8)  # 模擬生成的延遲感
            current_locations.append(loc)

            # 回傳累積的當日資料，讓前端即時畫線
            chunk = {
                "type": "data",
                "day": day_plan['day'],
                "location": loc,  # 最新的一個點
                "summary": day_plan['summary']
            }
            yield json.dumps(chunk) + "\n"

    yield json.dumps({"type": "status", "content": "行程規劃完成！"}) + "\n"


@app.get("/")
def read_root():
    return {"message": "Travel AI Agent API is running"}


@app.post("/api/plan")
async def plan_trip(prompt: str):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(ai_stream_generator(prompt), media_type="application/x-ndjson")

# 啟動指令: uv run uvicorn main:app --reload
