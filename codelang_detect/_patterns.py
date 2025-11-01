import re

# The compiled regex patterns should be defined at the module level so they are only compiled once when the module is imported.
PATTERNS = {
    'c': [
        # Highest confidence - strong C indicators (less common in modern C++)
        (re.compile(r'#include\s*<[a-z]+\.h>'), 5), # Includes with .h are very C-like (stdio.h, stdlib.h)
        (re.compile(r'\b(printf|scanf|malloc|free)\s*\('), 4), # Standard C library functions
        # High confidence
        (re.compile(r'^\s*#define\b'), 3), # Preprocessor directives (used in both, but very common in C)
        (re.compile(r'->\w+'), 2), # Struct pointer access
    ],
    'cbl': [
        (re.compile(r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\s*\.', re.IGNORECASE), 3),
        (re.compile(r'^\s*PROGRAM-ID\s*\.', re.IGNORECASE), 3),
        (re.compile(r'\s(PIC|PICTURE)\s+', re.IGNORECASE), 2),
    ],
    'cpp': [
        # Highest confidence - strong C++ indicators (distinguishes from C)
        (re.compile(r'#include\s*<(iostream|vector|string|map|memory)>'), 5), # C++ standard library headers without .h
        (re.compile(r'^\s*using\s+namespace\s+std;'), 4), # Very common in C++
        (re.compile(r'\bstd::\w+'), 4), # Use of the std namespace
        # High confidence
        (re.compile(r'^\s*class\s+\w+\s*\{'), 3), # Class keyword
        (re.compile(r'\b(public|private|protected):'), 3), # Access specifiers in classes
        (re.compile(r'template\s*<.*>'), 3), # Template syntax
    ],
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
    'dart': [
        # Highest confidence - unique Dart syntax
        (re.compile(r'^\s*import\s+["\']package:'), 5), # The 'package:' import is definitive
        (re.compile(r'\b(void|Future)\s+main\s*\(\)\s*(async)?'), 5), # Main entry point
        # High confidence
        (re.compile(r'\b(late|final|const)\s+\w+'), 4), # Common variable declarations
        (re.compile(r'@(override|required)\b'), 3), # Common annotations
        (re.compile(r'=>'), 2), # Fat arrow for single-line functions
    ],
    'go': [
        # Highest confidence - core Go syntax
        (re.compile(r'^\s*package\s+\w+'), 5), # package declaration is mandatory
        (re.compile(r'\bfunc\s+main\s*\(\)'), 5), # Main entry point
        (re.compile(r'\b(import\s+\(|import\s+["\']\w+)'), 4), # import "fmt" or import (...)
        (re.compile(r':='), 4), # Short variable declaration is highly idiomatic
        # High confidence
        (re.compile(r'\b(func|defer|go|chan)\b'), 3), # Unique keywords
        (re.compile(r'if\s+err\s*!=\s*nil'), 3), # Extremely common error handling pattern
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
    'kt': [
        (re.compile(r'\bdata\s+class\b'), 4),
        (re.compile(r'\bfun\b\s+.*\)\s*:\s*\w+'), 4),
        (re.compile(r'\bval\b\s+\w+\s*:'), 3),
        (re.compile(r'\s\?\:|\s\!\!\s'), 2),
    ],
    'php': [
        # Highest confidence - definitive PHP tags
        (re.compile(r'<\?php'), 5), # The opening tag is the strongest possible signal
        # High confidence - PHP-specific syntax
        (re.compile(r'\$\w+'), 4), # Variables are prefixed with $
        (re.compile(r'\b(echo|require_once|isset|unset)\b'), 3), # Common language constructs
        (re.compile(r'public\s+function\s+__\w+'), 3), # Magic methods like __construct
        (re.compile(r'->\w+'), 2), # Object operator
    ],
    'py': [
        (re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']\s*:'), 4),
        (re.compile(r'^\s*@\w+'), 3),
        (re.compile(r'\bself\b'), 3),
        (re.compile(r'^\s*(async\s+)?def\s+\w+\s*\(.*\)\s*:'), 2),
        (re.compile(r'\bfrom\b\s+[\w\.]+\s+\bimport\b'), 2),
    ],
    'r': [
        # Highest confidence - the most iconic R operators
        (re.compile(r'<-'), 5), # The assignment operator is almost exclusively R
        (re.compile(r'%>%'), 4), # The pipe operator (magrittr) is ubiquitous in modern R
        # High confidence - common functions and syntax
        (re.compile(r'\b(library|require)\s*\('), 3), # Loading packages
        (re.compile(r'\b(ggplot|dplyr|c|data\.frame)\b'), 2), # Very common functions/packages
    ],
    'ruby': [
        # Highest confidence - highly idiomatic Ruby
        (re.compile(r'\b(do|\{)\s*\|[^\|]+\|'), 5), # Block with arguments, e.g., `do |i|` or `{ |i| }`
        (re.compile(r':\w+'), 4), # Symbols, e.g., `:name`
        (re.compile(r'^\s*def\s+\w+'), 4), # Method definition
        # High confidence
        (re.compile(r'^\s*require\s+["\']'), 3), # Requiring gems
        (re.compile(r'\b(end|elsif|unless)\b'), 2), # Keywords
        (re.compile(r'^\s*class\s+\w+\s*<'), 2), # Inheritance syntax
    ],
    'rust': [
        # Highest confidence - core Rust syntax and idioms
        (re.compile(r'\bfn\s+main\s*\(\)'), 5), # Main entry point
        (re.compile(r'\blet\s+mut\b'), 5), # Mutable variable declaration is very Rust-specific
        (re.compile(r'^\s*use\s+[\w:]+;'), 4), # `use std::...` or `use crate::...`
        (re.compile(r'\w+!'), 4), # Macro usage like println!(), vec![]
        # High confidence
        (re.compile(r'\b(fn|let|const|struct|enum|impl|trait|pub)\b'), 3), # Common keywords
        (re.compile(r'::\s*<'), 2), # Turbofish syntax e.g., collect::<Vec<_>>()
    ],
    'scala': [
        (re.compile(r'\bcase\s+class\b'), 4),
        (re.compile(r'\b(val|var)\s+\w+\s*:\s*\w+\[\w+\]'), 4),
        (re.compile(r'\bdef\s+\w+\s*\(.*\)\s*:\s*\w+\s*='), 3),
        (re.compile(r'\bobject\b\s+\w+\s*(extends|\{)'), 3),
    ],
    'sh': [
        (re.compile(r'^\s*#!/bin/(bash|sh|zsh)'), 4),
        (re.compile(r'\$\{\w+\}|\$\w+'), 3),
        (re.compile(r'\b(then|fi|done)\b'), 3),
    ],
    'solidity': [
        # Highest confidence - absolutely unique to Solidity
        (re.compile(r'^\s*pragma\s+solidity\b'), 5), # Required in almost every file
        (re.compile(r'\bcontract\s+\w+\s*\{'), 5), # The core contract keyword
        # High confidence
        (re.compile(r'\b(uint\d*|address|mapping|payable)\b'), 4), # Solidity-specific types
        (re.compile(r'\b(require|revert|assert)\s*\('), 3), # Common functions
        (re.compile(r'\b(public|private|internal|external)\s+(pure|view)\b'), 3), # Visibility and state modifiers
    ],
    'sql': [
        (re.compile(r'^\s*(SELECT\s+.*\s+FROM|CREATE\s+TABLE|INSERT\s+INTO)\b', re.IGNORECASE), 4),
        (re.compile(r'\b(INNER|LEFT|RIGHT|FULL)\s+(OUTER\s+)?JOIN\b', re.IGNORECASE), 3),
        (re.compile(r'\b(GROUP|ORDER)\s+BY\b', re.IGNORECASE), 3),
    ],
    'swift': [
        (re.compile(r'\b(protocol|extension)\b\s+\w+'), 4),
        (re.compile(r'\b(func|struct|enum)\b\s+\w+'), 3),
        (re.compile(r'\)\s*->\s*\w+(?!\s*:)'), 3),
        (re.compile(r'\bimport\b\s+(UIKit|SwiftUI|Foundation)\b'), 3),
    ],
    'ts': [
        # Highest confidence - TypeScript-only syntax (distinguishes from JS)
        (re.compile(r'\b(interface|type)\s+\w+\s*='), 5), # Type/interface definitions
        (re.compile(r'\b(public|private|protected|readonly)\s+\w+'), 5), # Access modifiers
        (re.compile(r':\s*(string|number|boolean|any|void)'), 4), # Type annotations
        # High confidence
        (re.compile(r'<\w+>'), 3), # Generic types, e.g., `Array<string>`
        (re.compile(r'\benum\s+\w+\s*\{'), 3), # Enum definition
    ],
    'yaml': [
        (re.compile(r'^---'), 4),
        (re.compile(r'^\s*[\w\.-]+:\s+.*'), 3),
        (re.compile(r'^\s*-\s+'), 2),
    ],
}