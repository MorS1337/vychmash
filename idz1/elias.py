def bin_wo_prefix(n):
    return format(n, 'b')

def elias_gamma_encode(n: int) -> str:
    assert n >= 1
    b = bin_wo_prefix(n)
    return '0' * (len(b) - 1) + b

def elias_gamma_decode(bits: str, i=0):
    z = 0
    while i < len(bits) and bits[i] == '0':
        z += 1
        i += 1
    if i + z >= len(bits):
        raise ValueError("Укороченная запись")
    n = int('1' + bits[i+1:i+z+1], 2)
    return n, i + z + 1

def elias_delta_encode(n: int) -> str:
    assert n >= 1
    b = bin_wo_prefix(n)
    L = len(b)
    gL = elias_gamma_encode(L)
    return gL + b[1:]

def elias_delta_decode(bits: str, i=0):
    L, i = elias_gamma_decode(bits, i)
    if L == 1:
        return 1, i
    if i + (L-1) > len(bits): raise ValueError("truncated tail in delta")
    n = int('1' + bits[i:i+L-1], 2)
    return n, i+(L-1)

