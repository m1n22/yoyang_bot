from fastapi import FastAPI, Request

app = FastAPI()

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

# 혈압 수치에 따라 상태 문구를 만들어주는 함수
def analyze_blood_pressure(bp_text: str) -> str:
    bp_str = str(bp_text).strip()
    
    # '정상' 같은 문자가 직접 들어왔을 경우
    if "/" not in bp_str:
        return f"혈압은 {bp_str} 수준으로 특이사항 없이 양호함"

    try:
        # 수축기/이완기 수치 분리 (예: "132/94" -> sys=132, dia=94)
        sys_str, dia_str = bp_str.split("/")
        sys = int(sys_str.strip())
        dia = int(dia_str.strip())
        josa = get_josa_ro(bp_str)

        # 수치 판단 기준
        if sys >= 140 or dia >= 90:
            status = "고혈압 수치가 확인되어 지속적인 주의 관찰이 필요함"
        elif sys >= 130 or dia >= 80:
            status = "혈압이 다소 높은 편으로 모니터링을 진행함"
        elif sys < 90 or dia < 60:
            status = "저혈압 경향이 있어 휴식 및 상태를 관찰함"
        else:
            status = "정상 범주 내에 있어 건강 상태 양호함"

        return f"혈압은 {bp_str}{josa} {status}"

    except Exception:
        # 수치 해석 실패 시 기본 문구
        josa = get_josa_ro(bp_str)
        return f"혈압은 {bp_str}{josa} 확인됨"

@app.post("/")
async def create_record(request: Request):
    body = await request.json()
    params = body.get('action', {}).get('params', {})
    
    # 1. 카카오톡에서 파라미터 값 수신
    meal = params.get('meal_amount', '전량')
    bp = params.get('blood_pressure', '120/80')

    # 2. 식사량 단어 정돈 ("1/2 섭취" -> "1/2")
    clean_meal = meal.replace("섭취", "").strip()
    if clean_meal in ["전량", "1/2", "1/3", "2/3"]:
        meal_text = f"식사는 {clean_meal} 섭취하셨습니다."
    else:
        meal_text = f"식사는 {clean_meal}하셨습니다."

    # 3. 혈압 상태 자동 분석 문장 생성
    bp_result_text = analyze_blood_pressure(bp)

    # 4. 최종 보고서 문장 완성
    final_record = f"방문 시 식사 보조를 제공하였으며, {meal_text} 건강 상태 점검 결과 {bp_result_text}."

    # 5. 복사하기 편하도록 2개의 말풍선으로 분리 출력
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
                        "text": final_record
                    }
                }
            ]
        }
    }
