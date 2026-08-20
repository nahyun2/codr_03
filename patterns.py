"""[보너스 2] 패턴 생성기: 크기 N만 주면 십자가/X 패턴을 자동 생성."""

from core import create_grid


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
