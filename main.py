import os
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.post("/")
async def create_record(request: Request):
    body = await request.json()
    params = body.get('action', {}).get('params', {})
    
    # 카카오톡에서 보낸 버튼 값 받기
    meal = params.get('meal_amount', '전량')
    bp = params.get('blood_pressure', '정상')

    prompt = f"""
    당신은 노인장기요양보험 급여제공기록지를 작성하는 전문 요양보호사입니다.
    아래 전달된 기본 정보를 바탕으로, 장기요양급여 제공기록 보고서에 들어갈 깔끔하고 전문적인 문장을 작성해 주세요.

    [기본 정보]
    - 식사 보조 및 섭취량: {meal}
    - 건강 상태 및 혈압: {bp}

    [작성 규칙]
    - 정중하고 객관적인 요양보호 서비스 기록체(~함, ~하여 제공함 또는 ~하였습니다 체)로 작성해 주세요.
    - 식사 돌봄 내역과 건강 상태 확인 내역을 다듬어 자연스러운 2~3문장의 보고서 요약문으로 만들어 주세요.
    - 인사말이나 부연 설명 없이, 완성된 보고서 문구만 출력해 주세요.
    """

    try:
        # API 키 등록 여부 검증
        if not GEMINI_API_KEY:
            raise Exception("Render의 Environment 항목에 GEMINI_API_KEY가 등록되지 않았습니다.")

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        record_text = response.text.strip()
        
        # 정상 성공 시 2개 말풍선 분리 반환
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "📋 [급여제공기록 작성 완료]\n아래 문장만 복사해서 사용하세요!"
                        }
                    },
                    {
                        "simpleText": {
                            "text": record_text
                        }
                    }
                ]
            }
        }

    except Exception as e:
        # 💡 에러 발생 시 원인을 카카오톡 메시지로 직접 출력합니다.
        error_message = f"🚨 Gemini 연동 실패 원인:\n{str(e)}"
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": error_message
                        }
                    }
                ]
            }
        }
