import math, random
import numpy as np
import pandas as pd
from statistics import mean
from typing import Tuple, Callable, List
import os

from elias import bin_wo_prefix, elias_gamma_encode, elias_gamma_decode, elias_delta_decode, elias_delta_encode
from rice import rice_encode, rice_decode
from fibonacci import fib_decode, fib_encode

# Быстрые тесты
def roundtrip_tests():
    # gamma/delta
    for n in [1,2,3,4,5,7,13,31,32,33,127,128,129,999,1024]:
        g = elias_gamma_encode(n); n2, _ = elias_gamma_decode(g, 0); assert n==n2, f"Ошибка гамма {n}"
        d = elias_delta_encode(n); n3, _ = elias_delta_decode(d, 0); assert n==n3, f"Ошибка дельта {n}"
    # rice
    for k in range(0,7):
        for n in [0,1,2,3,4,5,7,13,31,32,33,127,128,129,999,1024]:
            r = rice_encode(n, k); n2, _ = rice_decode(r, 0, k); assert n==n2, f"Ошибка rice n={n}, k={k}"
    # fibonacci (n >= 1)
    for n in [1,2,3,4,5,7,13,31,32,33,127,128,129,999,1024]:
        f = fib_encode(n)
        n2, _ = fib_decode(f, 0)
        assert n==n2, f"Ошибка fib {n}"
            
roundtrip_tests()

# -----------------------------
# Распределение
# -----------------------------

def sample_geometric(N: int, p: float, rng=None) -> List[int]:
    rng = rng or random
    out = []
    for _ in range(N):
        u = rng.random()
        n = 1 + math.floor(math.log(1-u)/math.log(1-p))
        out.append(n)
    return out

def sample_pareto_heavy_tail(N: int, alpha: float, xmin: int = 1, rng=None) -> List[int]:
    # Распределение Парето
    rng = rng or random
    out = []
    for _ in range(N):
        u = rng.random()
        x = xmin / ((1 - u) ** (1/alpha))  # Pareto(alpha, xmin)
        n = max(1, int(x))
        out.append(n)
    return out

def sample_mixed(N: int, rng=None) -> List[int]:
    # Обычно малые 1..10, но иногда бывают спайки на 1000+
    rng = rng or random
    out = []
    for _ in range(N):
        if rng.random() < 0.85:
            out.append(rng.randint(1, 10))
        else:
            # 15% шанс спайка
            out.append(int(10 ** rng.uniform(2, 4)))  # 100..10000
    return out

def sample_uniform_bounded(N: int, low: int, high: int, rng=None) -> List[int]:
    rng = rng or random
    return [rng.randint(low, high) for _ in range(N)]

# -----------------------------
# Эксперимент
# -----------------------------

def avg_len_bits(sample: List[int], enc_fn: Callable[[int], str]) -> float:
    total = 0
    for x in sample:
        bits = enc_fn(int(x))
        total += len(bits)
    return total / len(sample)

def evaluate(sample: List[int], name: str, rice_k_max: int = 10, fixed_bits: int = 16):
    results = []
    L_fixed = fixed_bits
    results.append((name, 'Fixed', f'{fixed_bits}b', L_fixed))

    L_gamma = avg_len_bits(sample, elias_gamma_encode)
    results.append((name, 'Elias-γ', '-', L_gamma))

    L_delta = avg_len_bits(sample, elias_delta_encode)
    results.append((name, 'Elias-δ', '-', L_delta))

    # Fibonacci (для n>=1)
    L_fibo = avg_len_bits(sample, fib_encode)
    results.append((name, 'Fibonacci', '-', L_fibo))

    best_rice_len = None
    best_k = None
    for k in range(0, rice_k_max+1):
        L_rice = avg_len_bits(sample, lambda n: rice_encode(max(n-1,0), k))
        results.append((name, 'Rice', f'k={k}', L_rice))
        if best_rice_len is None or L_rice < best_rice_len:
            best_rice_len = L_rice; best_k = k

    df = pd.DataFrame(results, columns=['распределение','кодирование','параметры','среднее битов'])
    df['compression_vs_fixed'] = L_fixed / df['среднее битов']
    df['note'] = ''
    df.loc[(df['кодирование']=='Rice') & (df['параметры']==f'k={best_k}'), 'note'] = 'best Rice'
    return df, best_k, best_rice_len

# Масштабирование для больших данных
random.seed(1337)
np.random.seed(1337)

N = 100_000

datasets = {
    'Geom p=0.20': sample_geometric(N, p=0.20),
    'Geom p=0.10': sample_geometric(N, p=0.10),
    'Heavy (Pareto α=1.2)': sample_pareto_heavy_tail(N, alpha=1.2, xmin=1),
    'Mixed small+spikes': sample_mixed(N),
    'Uniform 1..100': sample_uniform_bounded(N, 1, 100),
}

all_results = []
best_params = []

for name, sample in datasets.items():
    df, best_k, best_len = evaluate(sample, name, rice_k_max=10, fixed_bits=16)
    all_results.append(df)
    best_params.append((name, best_k, best_len))

summary = pd.concat(all_results, ignore_index=True)

# Для rice-кодирования находим наилучший k
def best_rice_rows(df):
    grouped = df[df['кодирование']=='Rice'].copy()
    best = grouped.loc[grouped.groupby('распределение')['среднее битов'].idxmin()]
    return best

best_rice = best_rice_rows(summary)
best_rice = best_rice_rows(summary)
core = pd.concat([
    summary[summary['кодирование']=='Fixed'],
    summary[summary['кодирование']=='Elias-γ'],
    summary[summary['кодирование']=='Elias-δ'],
    summary[summary['кодирование']=='Fibonacci'],
    best_rice
], ignore_index=True)


core = core.sort_values(['распределение','кодирование']).reset_index(drop=True)

# Save CSVs
from pathlib import Path

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

full_path = OUT / "full_results.csv"
core_path = OUT / "summary_core.csv"

summary.to_csv(full_path, index=False)
core.to_csv(core_path, index=False)

print("Saved:")
print(f" - Full results: {full_path}")
print(f" - Core summary: {core_path}")

