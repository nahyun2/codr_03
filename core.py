"""핵심 로직: 데이터 구조(2D/1D), MAC 연산(2D/1D), 라벨 정규화, 점수 판정."""

EPSILON = 1e-9          # 두 점수가 "사실상 같다"고 볼 허용오차 기준값 (부동소수점 오차 대응)


# =========================================================
# [Issue 1] 데이터 구조: n x n 2차원 배열 저장/조회
# =========================================================
def create_grid(n, fill=0.0):
    """n x n 크기의 2차원 리스트(list of list)를 만들어 반환한다."""
    # [n번 반복]을 바깥/안쪽 두 번 겹쳐서 "리스트 안에 리스트가 n개" 구조를 만든다.
    # 매 반복마다 새 리스트를 만들어야 하며, 안 그러면(예: [[0]*n]*n) 모든 행이
    # 같은 리스트 객체를 참조하게 되어 한 칸만 바꿔도 모든 행이 같이 바뀌는 버그가 생긴다.
    return [[fill] * n for _ in range(n)]


def get_cell(grid, row, col):
    """grid의 (row, col) 위치 값을 반환한다."""
    return grid[row][col]   # 바깥 인덱스가 행(row), 안쪽 인덱스가 열(col)


def set_cell(grid, row, col, value):
    """grid의 (row, col) 위치에 value를 저장한다."""
    grid[row][col] = value  # 해당 위치의 원소를 새 값으로 덮어씀 (파이썬 리스트는 mutable)


# =========================================================
# [보너스 1] 데이터 구조 1차원 버전 (메모리 접근 단순화)
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


def mac_operation_1d(pattern_1d, filter_1d):
    """1차원 배열 버전 MAC 연산. 인덱스 계산 없이 리스트를 한 번만 순회한다."""
    score = 0.0
    for i in range(len(pattern_1d)):
        score += pattern_1d[i] * filter_1d[i]
        # 2차원 버전은 grid[row][col]처럼 인덱싱을 두 번 거치는데,
        # 1차원은 grid[i] 한 번만 거치면 되고, 메모리도 연속적이라 캐시 활용이 더 좋다.
    return score


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
