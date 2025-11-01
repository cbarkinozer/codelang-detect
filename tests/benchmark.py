import re
import timeit
from collections import defaultdict

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
        
    patterns = {
        'cs': [
            (re.compile(r'\{\s*get;\s*set;\s*\}'), 5),
            (re.compile(r'\b(from|where|select)\s+\w+\s+\b(in|select|group)\b'), 4),
            (re.compile(r'^\s*\[\w+\]'), 4),
            (re.compile(r'\busing\s*\('), 4),
            (re.compile(r'\busing\s+System(\.\w+)*;'), 3),
            (re.compile(r'\w+\s*=>\s*\w+'), 3),
            (re.compile(r'\bnamespace\s+[\w\.]+'), 2),
            (re.compile(r'\b(string|bool|int|double|var)\b'), 1),
        ],
        'java': [
            (re.compile(r'\bboolean\b'), 5),
            (re.compile(r'public\s+static\s+void\s+main\s*\(\s*String\[\]\s*args\s*\)'), 4),
            (re.compile(r'^\s*@\w+'), 4),
            (re.compile(r'\bObjects\.nonNull\b'), 3),
            (re.compile(r'\bimport\s+java\.\w+\.\w+;'), 3),
        ],
        'js': [
            (re.compile(r'\b(const|let|var)\s+[\w\s,]+\s*=\s*\(?[\w\s,]*\)?\s*=>'), 4),
            (re.compile(r'\b(const|let)\s+\w+\s*='), 3),
            (re.compile(r'\basync\s+function\b|\basync\s+\w+\s*=>'), 3),
            (re.compile(r'console\.(log|warn|error)\s*\('), 2),
        ],
        'py': [
            (re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']\s*:'), 4),
            (re.compile(r'^\s*@\w+'), 3),
            (re.compile(r'\bself\b'), 3),
            (re.compile(r'^\s*(async\s+)?def\s+\w+\s*\(.*\)\s*:'), 2),
            (re.compile(r'\bfrom\b\s+[\w\.]+\s+\bimport\b'), 2),
        ],
        'yaml': [
            (re.compile(r'^---'), 4),
            (re.compile(r'^\s*[\w\.-]+:\s+.*'), 3),
            (re.compile(r'^\s*-\s+'), 2),
        ],
        'sh': [
            (re.compile(r'^\s*#!/bin/(bash|sh|zsh)'), 4),
            (re.compile(r'\$\{\w+\}|\$\w+'), 3),
            (re.compile(r'\b(then|fi|done)\b'), 3),
        ],
        'kt': [
            (re.compile(r'\bdata\s+class\b'), 4),
            (re.compile(r'\bfun\b\s+.*\)\s*:\s*\w+'), 4),
            (re.compile(r'\bval\b\s+\w+\s*:'), 3),
            (re.compile(r'\s\?\:|\s\!\!\s'), 2),
        ],
        'cbl': [
            (re.compile(r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\s*\.', re.IGNORECASE), 3),
            (re.compile(r'^\s*PROGRAM-ID\s*\.', re.IGNORECASE), 3),
            (re.compile(r'\s(PIC|PICTURE)\s+', re.IGNORECASE), 2),
        ],
        'swift': [
            (re.compile(r'\b(protocol|extension)\b\s+\w+'), 4),
            (re.compile(r'\b(func|struct|enum)\b\s+\w+'), 3),
            (re.compile(r'\)\s*->\s*\w+(?!\s*:)'), 3),
            (re.compile(r'\bimport\b\s+(UIKit|SwiftUI|Foundation)\b'), 3),
        ],
        'sql': [
            (re.compile(r'^\s*(SELECT\s+.*\s+FROM|CREATE\s+TABLE|INSERT\s+INTO)\b', re.IGNORECASE), 4),
            (re.compile(r'\b(INNER|LEFT|RIGHT|FULL)\s+(OUTER\s+)?JOIN\b', re.IGNORECASE), 3),
            (re.compile(r'\b(GROUP|ORDER)\s+BY\b', re.IGNORECASE), 3),
        ],
        'scala': [
            (re.compile(r'\bcase\s+class\b'), 4),
            (re.compile(r'\b(val|var)\s+\w+\s*:\s*\w+\[\w+\]'), 4),
            (re.compile(r'\bdef\s+\w+\s*\(.*\)\s*:\s*\w+\s*='), 3),
            (re.compile(r'\bobject\b\s+\w+\s*(extends|\{)'), 3),
        ],
    }
    
    match_counts = defaultdict(int)
    for lang, rules in patterns.items():
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
    'csharp': 'cs',
    'c#': 'cs',
    'c-sharp': 'cs',
    'python': 'py',
    'python3': 'py',
    'javascript': 'js',
    'jsx': 'js',
    'shell': 'sh',
    'bash': 'sh',
    'yaml': 'yaml',
    'kotlin': 'kt',
    'cobol': 'cbl',
    'java': 'java',
    'sql': 'sql',
    'swift': 'swift',
    'scala': 'scala',
    'text': 'unknown',
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
code_samples = [
    {'id': 'cs_simple', 'expected': 'cs', 'code': "public class Game { public int Health { get; set; } }"},
    {'id': 'cs_lambda', 'expected': 'cs', 'code': 'Func<int, int> square = x => x * x;'},
    {'id': 'cs_full', 'expected': 'cs', 'code':"private string GetGitDiff() { try { var dte2 = (EnvDTE80.DTE2)ServiceProvider.GlobalProvider.GetService(typeof(EnvDTE.DTE)); using (var repo = new Repository(repositoryPath)) { var diff = repo.Diff.Compare<Patch>(repo.Head.Tip.Tree, DiffTargets.WorkingDirectory); return diff.Content; } } catch (Exception) { } }"},
    {'id': 'py_simple', 'expected': 'py', 'code': "import os\n\nif __name__ == '__main__':\n    print(f'Hello from {os.name}')"},
    {'id': 'py_class', 'expected': 'py', 'code':"class User:\n    def __init__(self, name: str, age: int):\n        self.name = name\n        self.age = age"},
    {'id': 'java_simple', 'expected': 'java', 'code': "import java.util.ArrayList; \n public class Test { // ... }"},
    {'id': 'java_full', 'expected': 'java', 'code': "public boolean checkIsAnyProductDeleted(Order order) { for (OrderItem orderItem : order.getOrderItemList()) { if (isProductDeleted) { productDeletedOfferFlag = true; } } return false; }"},
    {'id': 'js_arrow', 'expected': 'js', 'code': "const greet = (name) => console.log(`Hello, ${name}!`);"},
    {'id': 'yaml_k8s', 'expected': 'yaml', 'code': "apiVersion: v1\nkind: Pod\nmetadata:\n  name: mypod"},
    {'id': 'sh_shebang', 'expected': 'sh', 'code': "#!/bin/bash\nfor i in {1..5}; do\n  echo \"Welcome $i times\"\ndone"},
    {'id': 'kt_data_class', 'expected': 'kt', 'code': "data class User(val name: String, val age: Int)"},
    {'id': 'swift_func', 'expected': 'swift', 'code': "func greet(person: String) -> String {\n    return \"Hello, \\(person)!\"\n}"},
    {'id': 'scala_case_class', 'expected': 'scala', 'code': "case class Person(name: String, age: Int)"},
    {'id': 'sql_select', 'expected': 'sql', 'code': "SELECT user_id, user_name FROM users WHERE status = 'active' ORDER BY user_id;"},
    {'id': 'cbl_simple', 'expected': 'cbl', 'code': "IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\nPROCEDURE DIVISION.\nDISPLAY 'Hello world'.\nSTOP RUN."},
    {'id': 'plain_text', 'expected': 'unknown', 'code': "This is a sentence that is definitely not code."},
]

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