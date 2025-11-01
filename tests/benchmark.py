from collections import defaultdict
import os
import timeit
import json
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from codelang_detect import detect as detect_codelang
from codelang_detect._patterns import PATTERNS

try:
    from pygments.lexers import guess_lexer
    from pygments.util import ClassNotFound
    PYGMENTS_INSTALLED = True
except ImportError:
    PYGMENTS_INSTALLED = False

try:
    # 'whats-that-code' uses an "election" of multiple methods for accuracy.
    from whats_that_code.election import guess_language_all_methods
    WTC_INSTALLED = True
except ImportError:
    WTC_INSTALLED = False

# ==============================================================================
#  METHOD 1: Codelang-Detect (OUR IMPLEMENTATION)
# ==============================================================================

def detect_codelang(script: str) -> str:
    """Detect the programming language using a weighted custom regex system."""
    if not script or not script.strip():
        return 'unknown'
    
    match_counts = defaultdict(int)
    for lang, rules in PATTERNS.items():
        for regex, weight in rules:
            if regex.search(script):
                match_counts[lang] += weight
    
    if not match_counts or all(v == 0 for v in match_counts.values()):
        return 'unknown'
        
    return max(match_counts, key=match_counts.get)

# ==============================================================================
#  METHOD 2: WRAPPERS FOR COMPETITOR LIBRARIES
# ==============================================================================

# Central map to normalize all outputs to a consistent file extension.
LANG_ALIAS_MAP = {
    'bash': 'sh',
    'c': 'c',
    'c#': 'cs',
    'c++': 'cpp',
    'c-sharp': 'cs',
    'cbl': 'cbl',
    'cobol': 'cbl',
    'cpp': 'cpp',
    'cplusplus': 'cpp',
    'csharp': 'cs',
    'dart': 'dart',
    'go': 'go',
    'golang': 'go',
    'java': 'java',
    'javascript': 'js',
    'jsx': 'js',
    'kotlin': 'kt',
    'php': 'php',
    'python': 'py',
    'python3': 'py',
    'r': 'r',
    'ruby': 'rb',
    'rust': 'rust',
    'scala': 'scala',
    'shell': 'sh',
    'sol': 'sol',
    'solidity': 'sol',
    'sql': 'sql',
    'swift': 'swift',
    'text': 'unknown',
    'ts': 'ts',
    'tsx': 'ts',
    'typescript': 'ts',
    'yaml': 'yaml',
}

def detect_pygments(script: str) -> str:
    if not PYGMENTS_INSTALLED: return 'not_installed'
    if not script or not script.strip(): return 'unknown'
    try:
        lexer = guess_lexer(script)
        alias = lexer.aliases[0]
        return LANG_ALIAS_MAP.get(alias, alias)
    except (ClassNotFound, IndexError):
        return 'unknown'

def detect_whatsthatcode(script: str) -> str:
    if not WTC_INSTALLED: return 'not_installed'
    if not script or not script.strip(): return 'unknown'
    try:
        guess = guess_language_all_methods(script)
        return LANG_ALIAS_MAP.get(guess, 'unknown')
    except Exception:
        return 'unknown'

# ==============================================================================
#  BENCHMARK DATASET
# ==============================================================================

def load_code_samples():
    """Loads code samples from the test_data.json file."""
    # Construct a path relative to this script file
    script_dir = os.path.dirname(__file__)
    json_path = os.path.join(script_dir, 'test_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
code_samples = load_code_samples()


# ==============================================================================
#  BENCHMARK EXECUTION LOGIC
# ==============================================================================

def run_accuracy_benchmark(detectors):
    print("--- Accuracy Benchmark ---")
    header = f"| {'Test Case':<18} | {'Expected':<10} | " + " | ".join([f"{name:<22}" for name in detectors]) + " |"
    print(header)
    print("-" * len(header))

    scores = defaultdict(int)
    total_samples = len(code_samples)

    for sample in code_samples:
        expected = sample['expected']
        row = f"| {sample['id']:<18} | {expected:<10} |"
        
        for name, func in detectors.items():
            result = func(sample['code'])
            is_correct = result == expected
            if is_correct:
                scores[name] += 1
            
            status_symbol = "✅" if is_correct else "❌"
            row += f" {result:<19} {status_symbol} |"
        
        print(row)

    print("-" * len(header))
    print("\n--- Accuracy Summary ---")
    for name in detectors:
        accuracy = (scores[name] / total_samples) * 100 if total_samples > 0 else 0
        print(f"{name:<25}: {scores[name]}/{total_samples} correct ({accuracy:.1f}%)")

def run_performance_benchmark(detectors):
    print("\n\n--- Performance Benchmark ---")
    N_RUNS = 50  # Increased for more stable timing
    total_samples = len(code_samples)
    print(f"Running each detector {N_RUNS} times over {total_samples} samples...")

    for name, func in detectors.items():
        # Gracefully skip if the library for a detector isn't installed
        if func("") == 'not_installed':
            print(f"\nDetector: {name:<25} (Not installed, skipping)")
            continue

        total_time = timeit.timeit(
            lambda: [func(sample['code']) for sample in code_samples],
            number=N_RUNS
        )
        
        avg_time_per_sample_us = (total_time / N_RUNS / total_samples) * 1_000_000
        
        print(f"\nDetector: {name:<25}")
        print(f"  Total time for {N_RUNS} runs: {total_time:.4f} seconds")
        print(f"  Avg time per sample: {avg_time_per_sample_us:.1f} µs (microseconds)")

if __name__ == "__main__":
    detectors_to_run = {
        'Codelang-Detect (Ours)': detect_codelang,
        'Pygments': detect_pygments,
        'WhatsThatCode': detect_whatsthatcode,
    }

    run_accuracy_benchmark(detectors_to_run)
    run_performance_benchmark(detectors_to_run)