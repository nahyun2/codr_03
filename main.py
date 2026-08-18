import json   # data.json 파일을 파이썬 dict로 읽어오기 위한 표준 라이브러리
import sys    # 콘솔 출력 인코딩을 강제로 UTF-8로 맞추기 위해 사용
import time   # 연산 시간을 측정하기 위한 표준 라이브러리 (perf_counter 사용)

# Windows 콘솔의 기본 인코딩(cp949)에서는 '✓' 같은 유니코드 문자를 출력하다가
# UnicodeEncodeError로 프로그램이 죽을 수 있다. 표준출력/표준입력을 UTF-8로 재설정해 방지한다.
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

EPSILON = 1e-9          # 두 점수가 "사실상 같다"고 볼 허용오차 기준값 (부동소수점 오차 대응)
DATA_JSON_PATH = "data.json"   # 모드 2에서 읽어올 JSON 파일 경로


# =========================================================
# [Issue 1] 데이터 구조: n x n 2차원 배열 저장/조회
# =========================================================
def create_grid(n, fill=0.0):
    """n x n 크기의 2차원 리스트(list of list)를 만들어 반환한다."""
    # [n번 반복]을 바깥/안쪽 두 번 겹쳐서 "리스트 안에 리스트가 n개" 구조를 만든다.
    # 매 반복마다 새 리스트를 만들어야 하며, 안 그러면(예: [[0]*n]*n) 모든 행이
    # 같은 리스트 객체를 참조하게 되어 한 칸만 바꿔도 모든 행이 같이 바뀌는 버그가 생긴다.
    return [[fill for _ in range(n)] for _ in range(n)]


def get_cell(grid, row, col):
    """grid의 (row, col) 위치 값을 반환한다."""
    return grid[row][col]   # 바깥 인덱스가 행(row), 안쪽 인덱스가 열(col)


def set_cell(grid, row, col, value):
    """grid의 (row, col) 위치에 value를 저장한다."""
    grid[row][col] = value  # 해당 위치의 원소를 새 값으로 덮어씀 (파이썬 리스트는 mutable)


# =========================================================
# [Issue 2] 모드 1: 콘솔 입력 + 검증
# =========================================================
def read_grid_from_console(n, label):
    """
    n줄을 입력받아 n x n grid를 만들어 반환한다.
    - 각 줄은 공백으로 구분된 n개의 숫자여야 한다.
    - 행 개수/열 개수 불일치, 숫자 파싱 실패 시 에러 메시지를 출력하고 다시 입력받는다.
    """
    while True:
        # while True + 맨 아래의 continue/return 조합으로 "검증 실패 시 재입력" 흐름을 만든다.
        print(f"{label} ({n}줄 입력, 공백 구분)")
        rows = []      # 검증을 통과한 각 행(숫자 리스트)을 순서대로 담을 리스트
        ok = True       # 지금까지 입력받은 줄들이 전부 유효했는지 나타내는 플래그

        for _ in range(n):
            # n번 반복하며 한 줄씩 입력을 받는다 (3x3이면 3번, 5x5면 5번 ...)
            line = input().strip()
            # input(): 사용자가 콘솔에 입력한 한 줄을 문자열로 받아온다.
            # .strip(): 줄 앞뒤에 실수로 들어간 공백/줄바꿈을 제거한다.

            values = line.split()
            # 공백을 기준으로 문자열을 쪼개 리스트로 만든다. "0 1 0" -> ["0", "1", "0"]

            if len(values) != n:
                # 값의 개수가 n개가 아니면(너무 적거나 많으면) 이 줄은 형식이 틀린 것
                ok = False
                break   # 더 이상 진행할 필요 없으므로 입력 루프를 즉시 중단

            try:
                row = [float(v) for v in values]
                # values의 각 문자열을 float로 변환해서 새 리스트를 만든다.
                # "0" -> 0.0, "1.5" -> 1.5 처럼 실수로 바뀐다.
            except ValueError:
                # "가", "abc" 처럼 숫자로 바꿀 수 없는 값이 있으면 여기로 온다.
                ok = False
                break

            rows.append(row)
            # 이번 줄은 검증을 통과했으므로 rows 리스트 맨 뒤에 추가한다.

        if not ok or len(rows) != n:
            # 도중에 실패했거나(ok=False), break로 일찍 빠져나와 행이 n개가 안 채워진 경우
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
            # while True의 맨 처음으로 돌아가 label을 다시 출력하고 재입력을 받는다.

        return rows
        # 여기 도달했다는 것은 n줄 모두 개수/형식 검증을 통과했다는 뜻 -> 완성된 grid 반환


# =========================================================
# [Issue 3] MAC (Multiply-Accumulate) 연산
# =========================================================
def mac_operation(pattern, filter_grid):
    """
    pattern과 filter_grid를 같은 위치끼리 곱한 뒤 모두 더해서 반환한다.
    NumPy 없이 반복문으로 직접 구현한다.
    """
    score = 0.0            # 누적 합계를 저장할 변수 (MAC의 'Accumulate' 부분)
    n = len(pattern)        # 격자 한 변의 길이. 3x3이면 n=3, 25x25면 n=25

    for row in range(n):          # 행을 하나씩 순회
        for col in range(n):      # 각 행 안에서 열을 하나씩 순회 -> 총 n*n번 반복
            score += pattern[row][col] * filter_grid[row][col]
            # 같은 위치(row, col)의 값끼리 곱하고(Multiply), score에 더한다(Accumulate).
            # 이 한 줄이 MAC 연산의 핵심이며, 이 반복이 n*n번 일어나므로 시간복잡도는 O(N^2)이다.

    return score   # 모든 위치의 곱을 다 더한 최종 유사도 점수


# =========================================================
# [Issue 4] 라벨 정규화 + 점수 비교(판정)
# =========================================================
def normalize_label(raw_label):
    """
    다양한 형태의 라벨을 표준 라벨('Cross' 또는 'X')로 변환한다.
    - '+' / 'cross' -> 'Cross'
    - 'x' / 'X'     -> 'X'
    """
    if raw_label is None:
        return None   # 값 자체가 없으면 정규화할 게 없으므로 None

    cleaned = str(raw_label).strip().lower()
    # str(): 혹시 숫자 등 다른 타입이 들어와도 문자열로 강제 변환 (방어적 처리)
    # strip(): 앞뒤 공백 제거, lower(): 대문자/소문자 표기를 하나로 통일 (예: 'X', 'x', ' X ' 모두 동일 취급)

    if cleaned in ("+", "cross"):
        return "Cross"   # data.json의 expected는 '+', filter 키는 'cross' -> 둘 다 표준 라벨 'Cross'로

    if cleaned == "x":
        return "X"        # expected의 'x', filter 키의 'x' -> 표준 라벨 'X'로

    return None   # 위 두 경우가 아니면 알 수 없는 라벨 (호출부에서 오류로 처리 가능하도록 None 반환)


def judge_scores(score_a, score_b, epsilon=EPSILON):
    """
    두 점수를 비교해서 'A', 'B', 'UNDECIDED' 중 하나를 반환한다.
    |score_a - score_b| < epsilon 이면 동점(UNDECIDED)으로 간주한다.
    """
    diff = abs(score_a - score_b)
    # 두 점수의 차이의 절댓값. 부동소수점 연산은 미세한 오차가 있을 수 있어
    # "완전히 같다(==)" 대신 "충분히 가깝다(diff < epsilon)"로 비교하는 것이 안전하다.

    if diff < epsilon:
        return "UNDECIDED"   # 차이가 허용오차보다 작으면 사실상 동점 -> 판정 불가

    if score_a > score_b:
        return "A"   # A가 더 크면 입력 패턴이 필터 A와 더 유사하다는 뜻

    return "B"   # 그 외의 경우(= B가 더 큼)


# =========================================================
# [Issue 6] 성능 측정
# =========================================================
def measure_mac_time_ms(pattern, filter_grid, repeat=10):
    """
    mac_operation을 repeat번 반복 실행하고, 평균 소요 시간(ms)을 반환한다.
    """
    start = time.perf_counter()
    # perf_counter(): 매우 정밀한 시각을 초 단위로 반환하는 시계 (시간 간격 측정 전용)

    for _ in range(repeat):
        mac_operation(pattern, filter_grid)
        # 반환값(점수)은 시간 측정 목적상 필요 없으므로 변수에 저장하지 않고 버린다.
        # I/O(입력/출력) 없이 순수 연산 함수만 반복 호출하는 구간을 측정하는 것이 핵심이다.

    end = time.perf_counter()

    total_seconds = end - start          # repeat번 반복하는 데 걸린 총 시간(초)
    avg_seconds = total_seconds / repeat  # 1회 평균 소요 시간(초)
    avg_ms = avg_seconds * 1000           # 초 -> 밀리초(ms) 변환 (1초 = 1000ms)

    return avg_ms


def print_performance_table(size_to_pattern_filter):
    """
    {size: (pattern, filter_grid)} 형태의 dict를 받아
    크기별 '평균 시간(ms)'과 '연산 횟수(N^2)'를 표로 출력한다.
    """
    print("크기       평균 시간(ms)    연산 횟수")
    print("-------------------------------------")

    for size in sorted(size_to_pattern_filter.keys()):
        # 3, 5, 13, 25 순서로 오름차순 정렬해서 출력 (표가 보기 좋도록)
        pattern, filter_grid = size_to_pattern_filter[size]
        # 이 크기(size)에 대응하는 (패턴, 필터) 튜플을 꺼내 각각의 변수로 분리(unpacking)

        avg_ms = measure_mac_time_ms(pattern, filter_grid, repeat=10)
        # 이 크기에서 MAC 연산을 10회 반복 측정한 평균 시간(ms)

        op_count = size * size
        # N x N 격자이므로 MAC 연산은 위치마다 한 번, 총 N^2번 일어난다.
        # 이것이 바로 "패턴 크기가 커지면 연산 시간이 O(N^2)로 늘어난다"의 근거 수치다.

        size_label = f"{size}x{size}"
        print(f"{size_label:<10} {avg_ms:>10.3f}    {op_count:>8}")
        # :<10 은 왼쪽 정렬 10칸, :>10.3f 는 오른쪽 정렬 10칸+소수점 3자리, :>8 은 오른쪽 정렬 8칸
        # (정렬 폭 숫자는 표를 보기 좋게 맞추기 위한 것일 뿐 로직과는 무관)


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


# =========================================================
# [보너스 1] 1차원 배열 최적화 (메모리 접근 단순화)
# =========================================================
def create_grid_1d(n, fill=0.0):
    """길이 n*n짜리 1차원 리스트를 만들어 반환한다. (n x n 격자를 한 줄로 편 것)"""
    return [fill for _ in range(n * n)]
    # 2차원처럼 "리스트 안에 리스트"가 아니라, 값들이 메모리에 쭉 이어진 리스트 하나뿐이다.


def get_cell_1d(grid, row, col, n):
    """1차원 grid에서 (row, col) 위치 값을 읽는다. row*n+col 공식으로 2차원 좌표를 1차원 인덱스로 바꾼다."""
    return grid[row * n + col]
    # 예: n=3일 때 (row=1, col=2) -> index = 1*3+2 = 5


def set_cell_1d(grid, row, col, n, value):
    """1차원 grid의 (row, col) 위치에 value를 저장한다."""
    grid[row * n + col] = value


def flatten_to_1d(grid_2d):
    """기존 2차원 grid(list of list)를 1차원 리스트로 변환한다."""
    n = len(grid_2d)
    flat = create_grid_1d(n)
    for row in range(n):
        for col in range(n):
            flat[row * n + col] = grid_2d[row][col]
    return flat


def mac_operation_1d(pattern_1d, filter_1d):
    """1차원 배열 버전 MAC 연산. 인덱스 계산 없이 리스트를 한 번만 순회한다."""
    score = 0.0
    for i in range(len(pattern_1d)):
        score += pattern_1d[i] * filter_1d[i]
        # 2차원 버전은 grid[row][col]처럼 인덱싱을 두 번 거치는데,
        # 1차원은 grid[i] 한 번만 거치면 되고, 메모리도 연속적이라 캐시 활용이 더 좋다.
    return score


def measure_mac_time_ms_1d(pattern_1d, filter_1d, repeat=10):
    """mac_operation_1d를 repeat번 반복해 평균 소요 시간(ms)을 반환한다. (2차원 버전과 동일한 측정 방식)"""
    start = time.perf_counter()
    for _ in range(repeat):
        mac_operation_1d(pattern_1d, filter_1d)
    end = time.perf_counter()
    return (end - start) / repeat * 1000


def print_1d_vs_2d_comparison(size_to_pattern_filter):
    """
    동일한 입력, 동일한 반복 횟수(10회)로 2차원 버전과 1차원 버전의 MAC 연산 속도를 비교해 표로 출력한다.
    """
    print("크기       2D 평균(ms)    1D 평균(ms)    배율(2D/1D)")
    print("--------------------------------------------------")
    for size in sorted(size_to_pattern_filter.keys()):
        pattern, filter_grid = size_to_pattern_filter[size]

        ms_2d = measure_mac_time_ms(pattern, filter_grid, repeat=10)
        # 기존 [Issue 6]에서 만든 2차원 버전 측정 함수를 그대로 재사용

        pattern_1d = flatten_to_1d(pattern)
        filter_1d = flatten_to_1d(filter_grid)
        ms_1d = measure_mac_time_ms_1d(pattern_1d, filter_1d, repeat=10)

        ratio = ms_2d / ms_1d if ms_1d > 0 else float("inf")
        # ratio가 1보다 크면 1차원 버전이 더 빠르다는 뜻 (2D 시간을 1D 시간으로 나눈 배율)

        size_label = f"{size}x{size}"
        print(f"{size_label:<10} {ms_2d:>10.3f}    {ms_1d:>10.3f}    {ratio:>6.2f}x")


# =========================================================
# [보너스 2] 패턴 생성기: 크기 N만 주면 십자가/X 패턴을 자동 생성
# =========================================================
def generate_cross(n):
    """
    n x n 크기의 십자가(Cross) 패턴을 생성한다.
    정중앙 행 전체와 정중앙 열 전체를 1.0으로 채우고, 나머지는 0.0으로 둔다.
    create_grid와 같은 list-of-list 형식으로 반환하므로 mac_operation 등 기존 함수를 그대로 쓸 수 있다.
    """
    grid = create_grid(n, 0.0)
    center = n // 2   # 정수 나눗셈. n=5 -> center=2 (0,1,2,3,4 중 한가운데)

    for i in range(n):
        grid[center][i] = 1.0   # 정중앙 '행' 전체를 1로 채움 (가로줄)
        grid[i][center] = 1.0   # 정중앙 '열' 전체를 1로 채움 (세로줄)

    return grid


def generate_x(n):
    """
    n x n 크기의 X 패턴을 생성한다.
    좌상단->우하단 대각선과 우상단->좌하단 대각선을 1.0으로 채우고, 나머지는 0.0으로 둔다.
    """
    grid = create_grid(n, 0.0)

    for i in range(n):
        grid[i][i] = 1.0            # 좌상단 -> 우하단 대각선 (행=열)
        grid[i][n - 1 - i] = 1.0    # 우상단 -> 좌하단 대각선 (행+열 = n-1)

    return grid


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
    # (다른 파일에서 import main 할 때는 이 블록이 실행되지 않아, 함수만 따로 테스트할 수 있다.)
    main()
