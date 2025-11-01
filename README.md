# codelang-detect

🚀 A fast, lightweight, regex-based programming language detector for Python.

[![PyPI version](https://img.shields.io/pypi/v/codelang-detect.svg)](https://pypi.org/project/codelang-detect/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/codelang-detect/ci.yml?branch=main)](https://github.com/YOUR_USERNAME/codelang-detect/actions)
[![Python Versions](https://img.shields.io/pypi/pyversions/codelang-detect.svg)](https://pypi.org/project/codelang-detect/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

Codelang-detect identifies the programming language of a given code snippet. It is designed from the ground up to be **fast**, **accurate**, and have **zero external dependencies**. It's the perfect tool for pre-processing code, routing files, or any application where you need a quick and reliable language check without pulling in heavy libraries.

### Key Features

-   ⚡️ **Blazing Fast:** Built on a system of weighted, compiled regular expressions. Performance is measured in microseconds.
-   🎯 **Highly Accurate:** Demonstrably more accurate than popular alternatives on a curated suite of real-world and tricky code snippets.
-   📦 **Zero Dependencies:** Pure Python. `pip install codelang-detect` is all you need. No heavyweight models, no external binaries.
-   🔧 **Simple API:** A single function call: `detect(code)`.
-   💻 **CLI Included:** Use it directly from your terminal or in shell scripts.

### Why `codelang-detect`?

Many existing language detectors have significant trade-offs:

-   **Heavy ML Models (e.g., `guesslang`):** Often have complex or outdated dependencies (like older TensorFlow versions) that make installation difficult. They are also significantly slower for single detections.
-   **Comprehensive Tools (e.g., `pygments`):** Excellent for syntax highlighting, but its primary goal isn't detection. As the benchmarks show, its guessing can be unreliable.
-   **Platform-Specific Tools (e.g., GitHub's `linguist`):** The industry standard, but it's a Ruby Gem, making it difficult to integrate into a Python environment.

`codelang-detect` fills the gap for a "just right" solution: a lightweight, portable, and fast detector that delivers best-in-class accuracy.

### Benchmark: Accuracy & Performance

The results speak for themselves. On a [curated set of 16 code snippets](https://github.com/YOUR_USERNAME/codelang-detect/blob/main/benchmark.py) designed to test real-world accuracy, `codelang-detect` is both significantly more accurate and orders of magnitude faster than other popular libraries.

| Library                    | Accuracy  | Avg. Time / Sample (µs) | Dependencies     |
| -------------------------- | :-------: | :---------------------: | ---------------- |
| **`codelang-detect` (Ours)** | **100%**  |       **~65 µs**      | **None**         |
| `Pygments`                 |  12.5%    |       ~1460 µs        | None             |
| `WhatsThatCode`            |  18.8%    |       ~1804 µs        | None             |

*Benchmarks run on Python 3.13. Your results may vary.*

As the results show, `codelang-detect` is not only the most accurate solution in this test suite but also **~22x faster than `Pygments`** and **~27x faster than `WhatsThatCode`**, all while maintaining zero dependencies.

<details>
<summary>Click to see detailed accuracy breakdown</summary>

```
--- Accuracy Benchmark ---
| Test Case          | Expected   | Codelang-Detect (Ours) | Pygments               | WhatsThatCode          |
--------------------------------------------------------------------------------------------------------------
| cs_simple          | cs         | cs                  ✅ | text                ❌ | java                ❌ |
| cs_lambda          | cs         | cs                  ✅ | scdoc               ❌ | unknown             ❌ |
| cs_full            | cs         | cs                  ✅ | gdscript            ❌ | java                ❌ |
| py_simple          | py         | py                  ✅ | py                  ✅ | unknown             ❌ |
| py_class           | py         | py                  ✅ | perl6               ❌ | unknown             ❌ |
| java_simple        | java       | java                ✅ | py                  ❌ | java                ✅ |
| java_full          | java       | java                ✅ | teratermmacro       ❌ | unknown             ❌ |
| js_arrow           | js         | js                  ✅ | gdscript            ❌ | unknown             ❌ |
| yaml_k8s           | yaml       | yaml                ✅ | actionscript3       ❌ | unknown             ❌ |
| sh_shebang         | sh         | sh                  ✅ | sh                  ✅ | sh                  ✅ |
| kt_data_class      | kt         | kt                  ✅ | ssp                 ❌ | unknown             ❌ |
| swift_func         | swift      | swift               ✅ | gdscript            ❌ | unknown             ❌ |
| scala_case_class   | scala      | scala               ✅ | text                ❌ | cs                  ❌ |
| sql_select         | sql        | sql                 ✅ | scdoc               ❌ | unknown             ❌ |
| cbl_simple         | cbl        | cbl                 ✅ | componentpascal     ❌ | unknown             ❌ |
| plain_text         | unknown    | unknown             ✅ | unknown             ✅ | unknown             ✅ |
```

</details>

*Note: Libraries like `guesslang` and `enry` were excluded from the final benchmark due to significant installation issues with modern Python versions and their respective dependencies.*

### Installation

```bash
pip install codelang-detect
```

### Usage

#### As a Python Library

The API is dead simple. The `detect` function takes a string of code and returns the file extension of the detected language.

```python
from codelang_detect import detect

# Example 1: A Python snippet
python_code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
"""
lang = detect(python_code)
print(f"Detected language: {lang}")
# Output: Detected language: py

# Example 2: A C# snippet
csharp_code = "public class Person { public string Name { get; set; } }"
lang = detect(csharp_code)
print(f"Detected language: {lang}")
# Output: Detected language: cs

# Example 3: Ambiguous case
unknown_code = "This is just a regular sentence."
lang = detect(unknown_code)
print(f"Detected language: {lang}")
# Output: Detected language: unknown
```

#### As a Command-Line Tool (CLI)

You can also use `codelang-detect` directly from your terminal to analyze files.

```bash
# Analyze a file
codelang-detect my_script.js
# Output: js
```

It also supports reading from `stdin`, making it easy to pipe into.

```bash
# Pipe content into the CLI
cat deployment.yaml | codelang-detect
# Output: yaml
```

### Supported Languages

`codelang-detect` currently provides high-quality detection for the following languages. We welcome contributions to support additional languages; however, please note that expanding the list may reduce overall detection accuracy. To ensure quality, please demonstrate that the language you propose is both popular and genuinely needed.

-   C# (`cs`)
-   COBOL (`cbl`)
-   Java (`java`)
-   JavaScript (`js`)
-   Kotlin (`kt`)
-   Python (`py`)
-   Scala (`scala`)
-   Shell (`sh`)
-   SQL (`sql`)
-   Swift (`swift`)
-   YAML (`yaml`)

### How It Works

No magic here. `codelang-detect` uses a curated list of regular expressions for each language. Each regex is assigned a "weight" based on how uniquely it identifies a language.

For example:
-   The pattern ` { get; set; }` is a very strong signal for **C#** and gets a high weight.
-   The keyword `def` is a strong signal for **Python** but could also appear in Scala or Ruby, so it gets a moderate weight.
-   The keyword `int` is a weak signal, as it appears in many languages (C#, Java, C++), so it gets a very low weight.

The library runs all regexes against the input code, sums the weights for each language, and returns the language with the highest score. It's simple, transparent, and incredibly fast.

### Contributing

Contributions are welcome and appreciated! This project was started to fill a gap, and community help is the best way to make it the definitive tool for this job.

Whether it's improving regexes, adding support for a new language, or fixing a bug, please feel free to:

1.  [Open an issue](https://github.com/YOUR_USERNAME/codelang-detect/issues) to discuss the change.
2.  Fork the repository and submit a pull request.

Please see the `CONTRIBUTING.md` file for more details on setting up a development environment.

### License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.