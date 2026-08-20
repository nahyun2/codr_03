"""모드 1: 콘솔 입력 + 검증."""


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
