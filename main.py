from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/create-record")
async def create_record(request: Request):
    body = await request.json()
    params = body.get('action', {}).get('params', {})
    
    # 카카오톡에서 보낸 버튼 값 받기
    meal = params.get('meal_amount', '전량')
    bp = params.get('blood_pressure', '정상')

    # 문장 완성하기
    record_text = f"방문 시 식사 보조를 제공하였으며, 식사는 {meal} 섭취하셨습니다. 건강 상태 및 혈압은 {bp}(으)로 확인되었습니다."

    # 카카오톡으로 문장 보내기
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"📋 [자동 작성된 급여제공기록]\n\n{record_text}\n\n위 문장을 복사해서 사용하세요!"
                    }
                }
            ]
        }
    }
