# -----------------------------
# Fibonacci coding (n >= 1), биты идут от F2=1, F3=2, ... (low->high) + терминатор '1'
# Пример: 1->"11", 2->"011", 3->"0011", 4->"1011"
# -----------------------------

def _fib_list_upto(n: int):
    F = [1, 2]  # F2=1, F3=2
    while F[-1] <= n:
        F.append(F[-1] + F[-2])
    return F  # последний > n, рабочие индексы до len(F)-2

def fib_encode(n: int) -> str:
    assert n >= 1
    F = _fib_list_upto(n)
    j = len(F) - 2            # индекс наибольшего F_j <= n
    coeffs = [0]*(j+1)        # коэффициенты для F2..F_j (индекс 0 соответствует F2)
    rem = n
    prev_one = False
    # жадное разложение сверху вниз, без соседних единиц (Цеккендорф)
    while j >= 0:
        if F[j] <= rem and not prev_one:
            coeffs[j] = 1
            rem -= F[j]
            prev_one = True
        else:
            prev_one = False
        j -= 1
    # код: биты в порядке F2, F3, ... (от младших к старшим), затем терминатор '1'
    bits = ''.join('1' if b else '0' for b in coeffs) + '1'
    # убрать ведущие нули (если разложение началось не с F2)
    return bits

def fib_decode(bits: str, i: int = 0):
    # читаем биты F2, F3, ... слева направо; при встрече подряд '11' второй '1' — терминатор
    F = [1, 2]
    val = 0
    prev_one = False
    idx = 0  # 0 -> F2, 1 -> F3, ...
    L = len(bits)
    while i < L:
        b = bits[i]; i += 1
        if b == '1':
            if prev_one:
                # встретили '11' -> это стоп-бит, НЕ добавляем значение текущего F[idx]
                return val, i
            # обеспечиваем наличие F[idx]
            while idx >= len(F):
                F.append(F[-1] + F[-2])
            val += F[idx]
            prev_one = True
        else:
            prev_one = False
        idx += 1
    raise ValueError("truncated Fibonacci code")
