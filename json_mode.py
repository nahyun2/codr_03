"""모드 2: data.json 로드, 스키마 검증, 케이스별 판정, 결과 요약."""

import json

from core import EPSILON, judge_scores, mac_operation, normalize_label

DATA_JSON_PATH = "data.json"   # 모드 2에서 읽어올 JSON 파일 경로


# =========================================================
# [Issue 5] JSON 로드 + 스키마 검증 (모드 2)
# =========================================================
def load_data(path):
    """data.json 파일을 읽어서 dict로 반환한다."""
    with open(path, "r", encoding="utf-8") as f:
        # "r": 읽기 모드. encoding="utf-8": 한글 등이 깨지지 않도록 인코딩을 명시.
        # with문을 쓰면 블록이 끝날 때 파일이 자동으로 닫힌다 (자원 누수 방지).
        return json.load(f)
        # json.load(파일객체)는 JSON 텍스트를 파싱해서 파이썬 dict/list 구조로 변환한다.


def get_size_from_pattern_key(pattern_key):
    """
    'size_13_1' 같은 키에서 크기 N(=13)을 추출해서 int로 반환한다.
    형식이 이상하면 None을 반환한다(호출부에서 FAIL 처리).
    """
    try:
        parts = pattern_key.split("_")
        # "_"를 기준으로 문자열을 쪼갠다. "size_13_1" -> ["size", "13", "1"]
        return int(parts[1])
        # 두 번째 조각("13")을 정수로 변환해서 크기 N을 얻는다.
    except (IndexError, ValueError):
        # parts의 길이가 2 미만이면 parts[1]에서 IndexError,
        # 두 번째 조각이 숫자가 아니면 int() 변환에서 ValueError가 발생한다.
        return None
        # 두 경우 모두 "이 키에서는 크기를 알 수 없다"는 뜻이므로 None을 반환해
        # 프로그램이 죽지 않고 호출부에서 이 케이스를 FAIL 처리할 수 있게 한다.


def analyze_json_patterns(data):
    """
    data['patterns']의 각 케이스에 대해 크기 검증 -> MAC 연산 -> 판정 -> PASS/FAIL을 계산한다.
    개별 케이스에서 문제가 생겨도 전체 프로그램은 중단되지 않고, 그 케이스만 FAIL로 기록한다.
    """
    results = []   # 케이스별 결과 dict를 담을 리스트 (최종 반환값)

    filters = data.get("filters", {})    # data.json의 "filters" 항목 (없으면 빈 dict로 대체)
    patterns = data.get("patterns", {})  # data.json의 "patterns" 항목

    for case_key, case_data in patterns.items():
        # case_key 예: "size_5_1"
        # case_data 예: {"input": [[...]], "expected": "+"}
        try:
            size = get_size_from_pattern_key(case_key)
            if size is None:
                # 키 형식 자체가 이상해서 크기를 못 뽑아낸 경우 -> 이 케이스는 판별 불가능
                results.append({
                    "case": case_key, "cross_score": None, "x_score": None,
                    "verdict": None, "expected": None, "passed": False,
                    "reason": f"케이스 키 형식 오류: '{case_key}'에서 크기를 추출할 수 없음",
                })
                continue   # raise 하지 않고 다음 케이스로 넘어감 (프로그램이 죽지 않도록)

            filter_set = filters.get(f"size_{size}")
            if filter_set is None:
                # 이 패턴 크기에 맞는 필터 세트가 data.json에 없는 경우
                results.append({
                    "case": case_key, "cross_score": None, "x_score": None,
                    "verdict": None, "expected": None, "passed": False,
                    "reason": f"size_{size} 필터가 존재하지 않음",
                })
                continue

            pattern = case_data.get("input")
            size_mismatch = (
                pattern is None
                or len(pattern) != size                      # 행(row) 개수가 size와 다른 경우
                or any(len(row) != size for row in pattern)   # 어느 한 행이라도 열 개수가 다른 경우
            )
            if size_mismatch:
                results.append({
                    "case": case_key, "cross_score": None, "x_score": None,
                    "verdict": None, "expected": None, "passed": False,
                    "reason": f"패턴 크기가 size_{size} 필터와 일치하지 않음",
                })
                continue

            # filter_set의 키('cross', 'x')도 요구사항대로 normalize_label을 거쳐 표준 라벨로
            # 바꾼 뒤 매칭한다. 대소문자가 다르거나 표기가 조금 달라도(예: 'Cross') 안전하게 인식된다.
            normalized_filters = {}
            for raw_key, grid in filter_set.items():
                norm_key = normalize_label(raw_key)
                if norm_key:
                    normalized_filters[norm_key] = grid

            cross_filter = normalized_filters.get("Cross")
            x_filter = normalized_filters.get("X")
            if cross_filter is None or x_filter is None:
                # 정규화 후에도 'Cross' 또는 'X' 필터를 찾지 못한 경우의 스키마 오류
                results.append({
                    "case": case_key, "cross_score": None, "x_score": None,
                    "verdict": None, "expected": None, "passed": False,
                    "reason": f"size_{size} 필터 스키마 오류(cross/x 키 누락 또는 정규화 실패)",
                })
                continue

            # ---- 여기까지 왔다면 크기/스키마 검증을 모두 통과함 ----
            cross_score = mac_operation(pattern, cross_filter)
            x_score = mac_operation(pattern, x_filter)

            # judge_scores는 범용 함수라 'A'/'B'/'UNDECIDED'를 반환한다.
            # 여기서는 A자리에 cross_score, B자리에 x_score를 넣었으므로
            # 'A'는 Cross가 이겼다는 뜻, 'B'는 X가 이겼다는 뜻으로 해석해 표준 라벨로 바꿔준다.
            raw_verdict = judge_scores(cross_score, x_score, EPSILON)
            if raw_verdict == "A":
                verdict = "Cross"
            elif raw_verdict == "B":
                verdict = "X"
            else:
                verdict = "UNDECIDED"

            expected_norm = normalize_label(case_data.get("expected"))
            # JSON 원본의 expected는 '+' 나 'x' 같은 표기 -> 표준 라벨(Cross/X)로 정규화

            if verdict == "UNDECIDED":
                passed = False
                reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
            elif verdict == expected_norm:
                passed = True
                reason = None
            else:
                passed = False
                reason = f"판정({verdict})이 expected({expected_norm})와 다름"

            results.append({
                "case": case_key,
                "cross_score": cross_score,
                "x_score": x_score,
                "verdict": verdict,
                "expected": expected_norm,
                "passed": passed,
                "reason": reason,
            })

        except Exception as e:
            # 위에서 예상하지 못한 예외(예: 필터 내부 행 길이가 제각각이라 mac_operation에서
            # 인덱스 에러가 나는 경우 등)가 나더라도, 이 케이스만 FAIL로 남기고
            # 나머지 케이스 처리를 계속 진행한다 -> "프로그램 비정상 종료 금지" 요구사항 충족.
            results.append({
                "case": case_key, "cross_score": None, "x_score": None,
                "verdict": None, "expected": None, "passed": False,
                "reason": f"예외 발생: {e}",
            })

    return results


# =========================================================
# [Issue 7] 결과 리포트 출력
# =========================================================
def print_summary(results):
    """
    results 리스트를 받아 총 테스트 수 / 통과 수 / 실패 수와
    실패 케이스 목록(식별자 + 사유)을 출력한다.
    """
    total = len(results)
    # 전체 케이스 개수

    passed = sum(1 for r in results if r["passed"])
    # r["passed"]가 True인 것만 세어서 통과 개수를 구한다.
    # sum(1 for ... if 조건)은 "조건을 만족하는 개수 세기"에 자주 쓰이는 관용구.

    failed = total - passed
    # 전체에서 통과를 뺀 나머지가 실패 개수

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print()
        print("실패 케이스:")
        for r in results:
            if not r["passed"]:
                print(f"- {r['case']}: {r['reason']}")
                # 실패한 케이스마다 식별자와 사유를 한 줄씩 출력
