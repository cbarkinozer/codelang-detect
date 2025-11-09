import io
import sys
import pytest
from codelang_detect.cli import main

def test_cli_with_file_input(monkeypatch, capsys, tmp_path):
    """
    Tests the CLI by simulating running `codelang-detect <filename>`.
    """
    # Create a temporary file with some code in it
    test_file = tmp_path / "my_script.py"
    test_file.write_text("import os\nprint(os.name)")

    # Use monkeypatch to fake the command-line arguments
    # This simulates the user typing `codelang-detect my_script.py`
    monkeypatch.setattr(sys, 'argv', ['codelang-detect', str(test_file)])

    main()

    # Capture the output and assert it's correct
    captured = capsys.readouterr()
    assert captured.out == "py\n"
    assert captured.err == ""

def test_cli_with_stdin_pipe(monkeypatch, capsys):
    """
    Tests the CLI by simulating running `cat some_file.js | codelang-detect`.
    """
    # Prepare the code snippet to be "piped" in
    js_code = "const greet = () => console.log('Hello');"
    
    # Fake the command-line arguments (no file given)
    monkeypatch.setattr(sys, 'argv', ['codelang-detect'])

    # Fake sys.stdin to simulate piped input
    monkeypatch.setattr(sys, 'stdin', io.StringIO(js_code))

    main()

    # Capture the output and assert it's correct
    captured = capsys.readouterr()
    assert captured.out == "js\n"
    assert captured.err == ""

def test_cli_error_handling(monkeypatch, capsys):  # <-- Add monkeypatch here
    """
    Tests that the CLI exits gracefully when reading from stdin fails.
    """
    # Set clean arguments so pytest's args don't interfere
    monkeypatch.setattr(sys, 'argv', ['codelang-detect']) # <-- Add this line

    # Simulate a scenario where reading from a closed stdin fails
    sys.stdin.close()
    
    with pytest.raises(SystemExit) as e:
        main()
    
    # Check that the exit code is 1 (our custom error)
    assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Error: Could not process the input." in captured.err