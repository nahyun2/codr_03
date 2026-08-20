"""성능 측정(2D) + [보너스 1] 1차원 배열 최적화 비교."""

import time

from core import flatten_to_1d, mac_operation, mac_operation_1d


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
# [보너스 1] 1차원 배열 최적화 성능 비교
# =========================================================
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
        # 위쪽의 2차원 버전 측정 함수를 그대로 재사용

        pattern_1d = flatten_to_1d(pattern)
        filter_1d = flatten_to_1d(filter_grid)
        ms_1d = measure_mac_time_ms_1d(pattern_1d, filter_1d, repeat=10)

        ratio = ms_2d / ms_1d if ms_1d > 0 else float("inf")
        # ratio가 1보다 크면 1차원 버전이 더 빠르다는 뜻 (2D 시간을 1D 시간으로 나눈 배율)

        size_label = f"{size}x{size}"
        print(f"{size_label:<10} {ms_2d:>10.3f}    {ms_1d:>10.3f}    {ratio:>6.2f}x")
