import pytest
from codelang_detect import detect
import json
from pathlib import Path

# Test for basic, predictable edge cases to be sure it is working, the detailed testing is done in the benchmark
def test_detect_empty_string():
    """Should return 'unknown' for an empty string."""
    assert detect("") == 'unknown'

def test_detect_whitespace_only():
    """Should return 'unknown' for a string with only whitespace."""
    assert detect("   \n\t  ") == 'unknown'

def test_detect_plain_text():
    """Should return 'unknown' for a plain English sentence."""
    plain_text = "This is a regular sentence and should not be detected as code."
    assert detect(plain_text) == 'unknown'

def test_detect_simple_python():
    """A simple sanity check for a common language."""
    python_code = "def hello():\n    print('Hello')"
    assert detect(python_code) == 'py'


def load_test_data():
    """Loads test cases from the benchmark/test_data.json file."""
    # Assuming pytest is run from the repository root
    json_path = Path(__file__).parent.parent / "benchmark/test_data.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    # Format the data for pytest.mark.parametrize
    # We create a list of tuples: (code_snippet, expected_language, test_id)
    parametrized_data = []
    for case in test_cases:
        parametrized_data.append(
            pytest.param(
                case['code'], 
                case['expected'], 
                id=case['id']  # This makes test reports much more readable
            )
        )
    return parametrized_data


@pytest.mark.parametrize("code, expected_lang", load_test_data())
def test_detect_language_snippets(code, expected_lang):
    """
    Tests the detect function against the curated list of code snippets.
    This single function will run as multiple tests, one for each snippet.
    """
    detected_lang = detect(code)
    assert detected_lang == expected_lang