import os
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 한국어 받침 판별 함수 ('로' / '으로' 자동 구분)
def get_josa_ro(text: str) -> str:
    if not text:
        return "로"
    last_char = str(text)[-1]
    if last_char.isdigit():
        return "로" if last_char in ['2', '4', '5', '9'] else "으로"
    if '가' <= last_char <= '힣':
        code = ord(last_char) - 0xAC00
        jongseong = code % 28
        return "로" if jongseong in [0, 8] else "으로"
    return "로"

@app.post("/")
async def create_record(request: Request):
    body = await request.json()
    params = body.get('action', {}).get('params', {})
    
    # 카카오톡에서 보낸 파라미터 값 받기
    meal = params.get('meal_amount', '전량')
    bp = params.get('blood_pressure', '120/80')

    # 1. 식사량 입력값 정리 ("1/2 섭취" -> "1/2")
    clean_meal = meal.replace("섭취", "").strip()
    
    # 2. 혈압 조사 자동 구하기 (Fallback용)
    josa_ro = get_josa_ro(bp)

    # 💡 Gemini 프롬프트에 혈압 판단 로직 추가
    prompt = f"""
    당신은 노인장기요양보험 급여제공기록지를 작성하는 전문 요양보호사입니다.
    아래 전달된 기본 정보를 바탕으로, 장기요양급여 제공기록 보고서에 들어갈 깔끔하고 전문적인 문장을 작성해 주세요.

    [기본 정보]
    - 식사 보조 및 섭취량: {clean_meal}
    - 건강 상태 및 측정된 혈압 수치: {bp}

    [혈압 상태 판단 기준 및 작성 규칙]
    1. 수치 입력에 따른 혈압 상태 판정 기준:
       - 수축기(앞) 120 미만 AND 이완기(뒤) 80 미만: 정상 혈압 (양호함)
       - 수축기 120~130 미만 OR 이완기 80 미만: 주의/주의 관찰 필요
       - 수축기 130 이상 OR 이완기 80 이상: 고혈압 전단계 또는 고혈압 (주의 관찰 및 모니터링 필요)
       - 수축기 90 미만 OR 이완기 60 미만: 저혈압 (주의 관찰 필요)
       - 만약 '정상' 같은 단어만 입력되어 있다면 수치 판단 없이 정상 상태로 기록해 주세요.
    2. 작성 방식:
       - 정중하고 객관적인 요양보호 서비스 기록체(~함, ~하여 제공함 또는 ~하였습니다 체)로 작성해 주세요.
       - 식사 돌봄 내역과 혈압 측정 수치 및 상태(정상/주의/주의 관찰 등)를 종합하여 자연스러운 2~3문장의 보고서 요약문으로 만들어 주세요.
       - 인사말이나 부연 설명 없이, 완성된 보고서 문구만 출력해 주세요.
    """

    try:
        if not GEMINI_API_KEY:
            raise Exception("Render의 Environment 항목에 GEMINI_API_KEY가 등록되지 않았습니다.")

        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        record_text = response.text.strip()

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
        # Gemini 연동 실패 시 기본 예외 문구
        fallback_text = f"방문 시 식사 보조를 제공하였으며, 식사는 {clean_meal} 섭취하셨습니다. 건강 상태 및 혈압은 {bp}{josa_ro} 확인되었습니다."
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
                            "text": fallback_text
                        }
                    }
                ]
            }
        }
