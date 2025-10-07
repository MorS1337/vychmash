def rice_encode(n: int, k: int) -> str:
    assert n >= 0
    q = n >> k
    r = n & ((1<<k)-1)
    return '1'*q + '0' + (format(r, f'0{k}b') if k>0 else '')

def rice_decode(bits: str, i: int, k: int):
    L = len(bits)
    q = 0
    while i < L and bits[i] == '1':
        q += 1; i += 1
    if i >= L or bits[i] != '0': raise ValueError("missing rice stop bit")
    i += 1
    if k == 0: 
        return q, i
    if i + k > L: raise ValueError("truncated rice remainder")
    r = int(bits[i:i+k], 2)
    return (q<<k) + r, i+k
