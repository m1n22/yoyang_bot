import os
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

# 1. Gemini 클라이언트 설정 (발급받은 API 키를 넣어주세요)
# 환경변수로 관리하시거나, 직접 문자열로 "AIzaSy..." 넣어주셔도 됩니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

@app.post("/")
async def create_record(request: Request):
    body = await request.json()
    params = body.get('action', {}).get('params', {})
    
    # 카카오톡에서 보낸 버튼 값 받기
    meal = params.get('meal_amount', '전량')
    bp = params.get('blood_pressure', '정상')

    # 2. Gemini에게 전달할 프롬프트(지시사항) 작성
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
        # 3. Gemini 모델 호출 (gemini-2.5-flash 모델 사용)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        record_text = response.text.strip()
    except Exception as e:
        # 만약 API 호출 오류가 발생할 경우를 대비한 기본 문구 (예외 처리)
        record_text = f"방문 시 식사 보조를 제공하였으며, 식사는 {meal} 섭취하셨습니다. 건강 상태 및 혈압은 {bp}(으)로 확인되었습니다."

    # 4. 카카오톡으로 Gemini가 작성한 문장 보내기
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"📋 [Gemini 작성 급여제공기록]\n\n{record_text}\n\n위 문장을 복사해서 사용하세요!"
                    }
                }
            ]
        }
    }
