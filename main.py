"""Mini NPU Simulator - 진입점. 모드1/모드2 흐름을 연결한다.

기능은 core.py / io_console.py / json_mode.py / perf.py / patterns.py로 나뉘어 있고,
이 파일은 그 모듈들을 조합해 실제 실행 흐름(run_mode1, run_mode2, main)만 담당한다.
"""

import sys    # 콘솔 출력 인코딩을 강제로 UTF-8로 맞추기 위해 사용

from core import EPSILON, judge_scores, mac_operation, normalize_label
from io_console import read_grid_from_console
from json_mode import DATA_JSON_PATH, analyze_json_patterns, load_data, print_summary
from patterns import generate_cross, generate_x
from perf import measure_mac_time_ms, print_1d_vs_2d_comparison, print_performance_table

# Windows 콘솔의 기본 인코딩(cp949)에서는 '✓' 같은 유니코드 문자를 출력하다가
# UnicodeEncodeError로 프로그램이 죽을 수 있다. 표준출력/표준입력을 UTF-8로 재설정해 방지한다.
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")


# =========================================================
# 모드 1: 사용자 입력 (3x3) 흐름
# =========================================================
def run_mode1():
    """필터 A/B 입력 -> 저장 확인 -> 패턴 입력 -> MAC 연산 -> 판정 -> 성능 분석 순서로 실행."""

    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    filter_a = read_grid_from_console(3, "필터 A")
    filter_b = read_grid_from_console(3, "필터 B")
    print("✓ 필터 A, B 저장 완료")   # 요구사항: 필터 입력 -> "저장 확인" 단계

    print("\n#----------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = read_grid_from_console(3, "패턴")

    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")

    score_a = mac_operation(pattern, filter_a)   # 패턴과 필터 A의 유사도 점수
    score_b = mac_operation(pattern, filter_b)   # 패턴과 필터 B의 유사도 점수
    verdict = judge_scores(score_a, score_b, EPSILON)   # 'A' / 'B' / 'UNDECIDED'

    avg_ms = measure_mac_time_ms(pattern, filter_a, repeat=10)
    # 성능 분석(3x3): MAC 연산 1회를 10회 반복해서 평균 소요 시간(ms) 측정

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.3f} ms")

    if verdict == "UNDECIDED":
        print("판정: 판정 불가 (|A-B| < 1e-9)")
    else:
        print(f"판정: {verdict}")


# =========================================================
# 모드 2: data.json 분석 흐름
# =========================================================
def run_mode2():
    """필터 로드 -> 패턴 로드/검증 -> MAC/판정/PASS-FAIL -> 성능 분석 -> 결과 요약 순서로 실행."""

    data = load_data(DATA_JSON_PATH)   # data.json 전체를 dict로 읽어옴

    print("\n#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")
    filters = data.get("filters", {})
    for size_key in ("size_5", "size_13", "size_25"):
        # 요구사항에 명시된 필수 크기 3개를 순서대로 확인
        filter_set = filters.get(size_key)
        if filter_set:
            # filter_set의 원본 키('cross','x')를 normalize_label로 정규화해서
            # 실제로 어떤 라벨이 로드됐는지 데이터 기반으로 출력한다 (하드코딩 금지).
            labels = sorted({normalize_label(k) for k in filter_set.keys() if normalize_label(k)})
            print(f"✓ {size_key} 필터 로드 완료 ({', '.join(labels)})")
        else:
            print(f"✗ {size_key} 필터 없음")   # 없어도 프로그램은 계속 진행

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")
    results = analyze_json_patterns(data)   # 모든 패턴 케이스를 채점

    for r in results:
        print(f"--- {r['case']} ---")
        if r["cross_score"] is None:
            # 크기 불일치/스키마 오류 등으로 애초에 점수를 못 낸 케이스
            print(f"FAIL: {r['reason']}")
            continue
        print(f"Cross 점수: {r['cross_score']}")
        print(f"X 점수: {r['x_score']}")
        status = "PASS" if r["passed"] else f"FAIL ({r['reason']})"
        print(f"판정: {r['verdict']} | expected: {r['expected']} | {status}")

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")

    # data.json에는 3x3 필터가 없으므로, [보너스 2] 패턴 생성기로 3x3 십자가/X를 직접 만들어 쓴다.
    size_to_pattern_filter = {3: (generate_cross(3), generate_x(3))}
    # 5/13/25는 data.json에 있는 실제 cross/x 필터 쌍을 그대로 재사용해 순수 연산 시간만 측정한다.
    for size in (5, 13, 25):
        filter_set = filters.get(f"size_{size}")
        if filter_set:
            size_to_pattern_filter[size] = (filter_set["cross"], filter_set["x"])

    print_performance_table(size_to_pattern_filter)

    print("\n#----------------------------------------")
    print("# [보너스] 1차원 배열 최적화 비교 (동일 입력 / 동일 반복 횟수)")
    print("#----------------------------------------")
    print_1d_vs_2d_comparison(size_to_pattern_filter)

    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print_summary(results)


# =========================================================
# 진입점
# =========================================================
def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    choice = input("선택: ").strip()

    if choice == "1":
        run_mode1()
    elif choice == "2":
        run_mode2()
    else:
        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 main()을 호출한다.
    main()
