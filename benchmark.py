import re
import timeit
from collections import defaultdict

try:
    from pygments.lexers import guess_lexer
    from pygments.util import ClassNotFound
except ImportError:
    guess_lexer = None

try:
    from guesslang import Guess
    guess = Guess()
except ImportError:
    guess = None

try:
    from whatthelang import predict_lang
except ImportError:
    predict_lang = None

# Note: 'linguist' is a Ruby gem and difficult to integrate directly.
# It's better benchmarked via its file-based approach, not snippets.
# We will skip it in this direct snippet comparison for simplicity.

# --- 1. YOUR REGEX DETECTOR (Based on your screenshots) ---

def detect_language_regex(script: str) -> str:
    """
    Detect the programming language of the script using a weighted regex system.
    Returns the file extension as a string (e.g., 'py', 'cs').
    """
    # Define regex patterns with weights: (regex_pattern, weight)
    # Higher weight means a more confident indicator.
    # Using re.MULTILINE for ^ and $ to match start/end of lines.
    patterns = {
        'cs': [
            (re.compile(r'\bpublic\s+(static\s+)?void\s+Main\b'), 5), # Main entry point
            (re.compile(r'\bnamespace\s+[\w\.]+\b'), 4),
            (re.compile(r'\b(get|set);\s*}'), 5), # Auto-property syntax
            (re.compile(r'\busing\s+System(\.[\w]+)*;'), 4),
            (re.compile(r'\b(string|int|bool|double|var)\b'), 1), # Common types (lower weight)
        ],
        'java': [
            (re.compile(r'\bpublic\s+static\s+void\s+main\s*\(\s*String\[\]'), 5), # Classic main method
            (re.compile(r'\bimport\s+java\.\w+\.\w+;'), 4),
            (re.compile(r'\b(System\.out\.println|String|Integer)\b'), 2),
            (re.compile(r'@Override'), 4), # Annotation
            (re.compile(r'boolean'), 5), # 'boolean' is unique to Java vs C#'s 'bool'
        ],
        'py': [
            (re.compile(r'^\s*def\s+\w+\(.*\):'), 4),
            (re.compile(r'^\s*class\s+\w+\(.*\):'), 4),
            (re.compile(r'^\s*import\s+[\w\.]+'), 3),
            (re.compile(r'^\s*from\s+[\w\.]+\s+import'), 3),
            (re.compile(r'__name__\s*==\s*["\']__main__["\']'), 5), # Very Pythonic
            (re.compile(r'\[.*(for|if).*in.*\]'), 3), # List comprehension
        ],
        'js': [
            (re.compile(r'\b(const|let|var)\s+\w+\s*='), 3),
            (re.compile(r'\bfunction\s*\w*\s*\(.*\)\s*{'), 3),
            (re.compile(r'=>'), 4), # Arrow function syntax
            (re.compile(r'\b(console\.log|document\.getElementById)\b'), 4),
        ],
        'sh': [
            (re.compile(r'#!\s*/bin/(bash|sh|zsh)'), 10), # Shebang is definitive
            (re.compile(r'\b(echo|fi|esac|elif|then)\b'), 4),
            (re.compile(r'\$\w+|\$\{\w+\}'), 2), # Variable usage
        ],
        'yaml': [
            (re.compile(r'^\s*[\w\.-]+:\s+.*'), 2), # Key-value pair
            (re.compile(r'^\s*-\s+[\w\.-]+'), 3), # List item
            (re.compile(r'\b(apiVersion|kind|metadata|spec)\b'), 5), # K8s specific, very common
        ],
        'sql': [
            (re.compile(r'\b(SELECT|FROM|WHERE|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b', re.IGNORECASE), 5),
            (re.compile(r'\b(JOIN|LEFT\s+JOIN|INNER\s+JOIN)\b', re.IGNORECASE), 4),
        ],
        'scala': [
            (re.compile(r'\b(val|var)\s+\w+\s*:\s*\w+\s*='), 5), # Typed variable declaration
            (re.compile(r'\bdef\s+\w+\s*\[.*\]\s*\(.*\):'), 4), # Method with generics
            (re.compile(r'\b(object|case class)\s+\w+'), 5),
        ],
        'swift': [
            (re.compile(r'\b(let|var)\s+\w+\s*:\s*\w+'), 4), # Similar to Scala but common
            (re.compile(r'\bfunc\s+\w+\s*\(.*\)\s*->\s*\w+'), 5), # Function with return type arrow
            (re.compile(r'\b(import\s+UIKit|import\s+SwiftUI)\b'), 5),
        ],
        'kt': [
            (re.compile(r'\b(val|var)\s+\w+\s*:\s*\w+'), 4), # Kotlin/Scala overlap
            (re.compile(r'\bfun\s+\w+\s*\(.*\)\s*:\s*\w+'), 5), # `fun` keyword is distinctive
            (re.compile(r'package\s+[\w\.]+'), 3),
        ],
        'cbl': [
            (re.compile(r'^\s*IDENTIFICATION\s+DIVISION\.', re.IGNORECASE), 10), # Absolutely COBOL
            (re.compile(r'^\s*PROGRAM-ID\.', re.IGNORECASE), 10),
            (re.compile(r'\b(PERFORM|PIC|MOVE\s+TO|WORKING-STORAGE\s+SECTION)\b', re.IGNORECASE), 5),
        ]
    }

    match_counts = defaultdict(int)

    for lang, rules in patterns.items():
        for regex, weight in rules:
            if regex.search(script):
                match_counts[lang] += weight

    if not match_counts:
        return 'unknown'

    # Return the language with the highest score
    detected_language = max(match_counts, key=match_counts.get)
    return detected_language


# --- 2. WRAPPERS FOR COMPETITOR LIBRARIES ---

# Map competitor outputs to our standard extensions
LANG_MAP = {
    'csharp': 'cs', 'c#': 'cs',
    'java': 'java',
    'python': 'py',
    'javascript': 'js', 'jsx': 'js',
    'bash': 'sh', 'shell': 'sh',
    'yaml': 'yaml',
    'sql': 'sql',
    'scala': 'scala',
    'swift': 'swift',
    'kotlin': 'kt',
    'cobol': 'cbl',
    # Add more mappings as needed
}

def detect_pygments(script: str) -> str:
    if not guess_lexer: return 'not_installed'
    try:
        lexer = guess_lexer(script)
        # Pygments returns an alias, like 'csharp' or 'python'
        return LANG_MAP.get(lexer.aliases[0], 'unknown')
    except ClassNotFound:
        return 'unknown'

def detect_guesslang(script: str) -> str:
    if not guess: return 'not_installed'
    try:
        # Guesslang returns a full name, like 'C#' or 'Python'
        name = guess.language_name(script).lower()
        return LANG_MAP.get(name, 'unknown')
    except Exception:
        return 'unknown'

def detect_whatthelang(script: str) -> str:
    if not predict_lang: return 'not_installed'
    try:
        # whatthelang returns an extension directly, like 'py' or 'rb'
        return predict_lang(script)
    except Exception:
        return 'unknown'


# --- 3. BENCHMARK DATA AND EXECUTION ---

# Test samples designed to be tricky or idiomatic
code_samples = [
    {'id': 'csharp_1',   'expected': 'cs',   'code': 'public class Game { public int Health { get; set; } }'},
    {'id': 'java_1',     'expected': 'java', 'code': 'import java.util.ArrayList;\npublic class Test { // ... }'},
    {'id': 'python_1',   'expected': 'py',   'code': 'def main():\n    squares = {x: x*x for x in range(10)}'},
    {'id': 'js_1',       'expected': 'js',   'code': 'const greet = (name) => console.log(`Hello, ${name}!`);'},
    {'id': 'shell_1',    'expected': 'sh',   'code': '#!/bin/bash\nfor i in {1..5}; do\n  echo "Welcome $i times"\ndone'},
    {'id': 'yaml_1',     'expected': 'yaml', 'code': 'apiVersion: v1\nkind: Pod\nmetadata:\n  name: mypod'},
    {'id': 'sql_1',      'expected': 'sql',  'code': 'SELECT u.id, p.name FROM users u JOIN profiles p ON u.id = p.user_id;'},
    {'id': 'scala_1',    'expected': 'scala','code': 'case class Person(name: String, age: Int)'},
    {'id': 'swift_1',    'expected': 'swift','code': 'struct Person: View {\n    var body: some View {\n        Text("Hello")\n    }\n}'},
    {'id': 'kotlin_1',   'expected': 'kt',   'code': 'fun sum(a: Int, b: Int): Int {\n    return a + b\n}'},
    {'id': 'cobol_1',    'expected': 'cbl',  'code': 'IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\nPROCEDURE DIVISION.\nDISPLAY "Hello world".'},
    {'id': 'plain_text', 'expected': 'unknown','code': 'This is a sentence that is definitely not code.'},
]

def run_accuracy_benchmark(detectors):
    print("--- Accuracy Benchmark ---")
    header = f"{'ID':<12} | {'Expected':<10} | " + " | ".join([f"{name:<15}" for name in detectors])
    print(header)
    print("-" * len(header))

    scores = defaultdict(int)

    for sample in code_samples:
        expected = sample['expected']
        row = f"{sample['id']:<12} | {expected:<10} | "
        
        results = []
        for name, func in detectors.items():
            result = func(sample['code'])
            is_correct = result == expected
            if is_correct:
                scores[name] += 1
            
            # Add a checkmark for visual confirmation
            status_symbol = "✅" if is_correct else "❌"
            results.append(f"{result:<12} {status_symbol}")
        
        row += " | ".join(results)
        print(row)

    print("\n--- Accuracy Summary ---")
    for name in detectors:
        accuracy = (scores[name] / len(code_samples)) * 100
        print(f"{name:<20}: {scores[name]}/{len(code_samples)} correct ({accuracy:.1f}%)")


def run_performance_benchmark(detectors):
    print("\n\n--- Performance Benchmark ---")
    N_RUNS = 10  # Number of times to run the whole suite for timing
    
    print(f"Running each detector {N_RUNS} times over {len(code_samples)} samples...")

    for name, func in detectors.items():
        # Use timeit to get a precise timing
        total_time = timeit.timeit(
            lambda: [func(sample['code']) for sample in code_samples],
            number=N_RUNS
        )
        
        avg_time_per_sample_ms = (total_time / N_RUNS / len(code_samples)) * 1000
        print(f"{name:<20}: Average time per sample: {avg_time_per_sample_ms:.4f} ms")


if __name__ == "__main__":
    # Define the detectors to benchmark
    detectors_to_run = {
        'Your Regex Detector': detect_language_regex,
        'Pygments': detect_pygments,
        'Guesslang (TF)': detect_guesslang,
        'WhatTheLang': detect_whatthelang,
    }

    run_accuracy_benchmark(detectors_to_run)
    run_performance_benchmark(detectors_to_run)