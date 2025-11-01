import re
import timeit
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from whats_that_code.election import guess_language_all_methods

# ==============================================================================
#  METHOD 1: YOUR ORIGINAL REGEX-BASED DETECTOR
# ==============================================================================

def detect_language_regex(script: str) -> str:
    """Detect the programming language of the script using custom regex."""
    patterns = {
        'cs': [
            # Highest confidence - highly unique C# features
            (re.compile(r'\{\s*get;\s*set;\s*\}'), 5),  # Auto-property syntax (very high signal)
            (re.compile(r'\b(from|where|select)\s+\w+\s+\b(in|select|group)\b'), 4), # LINQ keywords
            (re.compile(r'^\s*\[\w+\]'), 4),  # Attributes like [ApiController]
            (re.compile(r'\busing\s*\('), 4), # using() statement for IDisposable is a definitive C# feature

            # High confidence
            (re.compile(r'\busing\s+System(\.\w+)*;'), 3), # Specific and common using statements
            (re.compile(r'\w+\s*=>\s*\w+'), 3), # C# Lambda expression
            (re.compile(r'\b(string|bool|int|double|var)\b'), 1), # C#-specific primitive types (lowercase)
            (re.compile(r'\bnamespace\s+[\w\.]+'), 2),

            # Medium confidence
            # CHANGED: Removed 'List<' which is too generic. 'Dictionary<' is more specific to C#.
            (re.compile(r'\bDictionary<'), 1),
            (re.compile(r'\bstring\[\]'), 1),
        ],
        'java': [
            # This is the most definitive signal. 'boolean' is unique to Java (vs C#'s 'bool').
            (re.compile(r'\bboolean\b'), 5),
            
            # Highest confidence - very specific to Java
            (re.compile(r'public\s+static\s+void\s+main\s*\(\s*String\[\]\s*args\s*\)'), 4), # Classic main method
            (re.compile(r'^\s*@\w+'), 4), # Annotations like @Override
            # A strong signal for modern Java.
            (re.compile(r'\bObjects\.nonNull\b'), 3),

            # High confidence
            (re.compile(r'\bimport\s+java\.\w+\.\w+;'), 3), # Standard Java library imports
            (re.compile(r'\bString\b'), 2), # Capitalized String is a strong Java indicator vs. C#'s 'string'
            (re.compile(r'^\s*package\s+[\w\.]+;'), 2),
            (re.compile(r'\b(implements|extends)\b'), 2),
            (re.compile(r'System\.out\.print(ln)?\s*\('), 2),
            (re.compile(r'\b(public|private|protected)\s+class\b'), 2), # Very common Java class declaration
            
            # Medium confidence
            (re.compile(r'\bfinal\b'), 1),
            # This is still a good signal for Java, as C# uses Dictionary, not HashMap.
            (re.compile(r'\b(ArrayList|HashMap)<'), 1),
        ],
        'js': [
            # Highest confidence - modern and unique JS syntax
            (re.compile(r'\b(const|let|var)\s+[\w\s,]+\s*=\s*\(?[\w\s,]*\)?\s*=>'), 4), # Arrow function assignment
            (re.compile(r'\b(const|let)\s+\w+\s*='), 3), # Modern variable declarations
            (re.compile(r'\basync\s+function\b|\basync\s+\w+\s*=>'), 3), # Async/await syntax
            # High confidence
            (re.compile(r'\bimport\b\s*\{?.*\}?\s*from\s*["\']'), 2), # ES6 imports
            (re.compile(r'require\s*\(\s*["\']'), 2), # CommonJS imports
            (re.compile(r'console\.(log|warn|error)\s*\('), 2), # Common console methods
            (re.compile(r'\bvar\s+\w+\s*='), 1), # Legacy variable declaration, distinguish from C#'s 'var'
            # Medium confidence
            (re.compile(r'\.then\s*\('), 1), # Promise syntax  
        ],
        'py': [
            # Highest confidence - highly idiomatic Python
            (re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']\s*:'), 4), # Main execution block
            (re.compile(r'^\s*@\w+'), 3), # Decorators
            (re.compile(r'\bself\b'), 3), # `self` is extremely common in Python classes
            (re.compile(r'f["\'][\s\w\{}]*["\']'), 3), # F-strings
            # High confidence
            (re.compile(r'^\s*(async\s+)?def\s+\w+\s*\(.*\)\s*:'), 2), # Function definition
            (re.compile(r'^\s*class\s+\w+\s*\(.*\)\s*:'), 2), # Class definition
            (re.compile(r'\bfrom\b\s+[\w\.]+\s+\bimport\b'), 2), # `from ... import` statements
            (re.compile(r'\[.*(for|if)\s+.*\s+in\s+.*\]'), 2), # List comprehension
        ],
        'yaml': [
            (re.compile(r'^---'), 4), # Document separator is a very strong signal
            (re.compile(r'^\s*[\w\.-]+:\s+.*'), 3),  # Key-value pairs must have a space after the colon
            (re.compile(r'^\s*-\s+'), 2), # List item
            (re.compile(r'^\s*[\w\.-]+:\s+'), 1), # Key-value, but anchored to line start and requiring a space after ':'
        ],
        'yml': [
            (re.compile(r'^---'), 4), # Document separator is a very strong signal
            (re.compile(r'^\s*[\w\.-]+:\s+.*'), 3),  # Key-value pairs must have a space after the colon
            (re.compile(r'^\s*-\s+'), 2), # List item
            (re.compile(r'\w+:\s*'), 1), # Generic key-value, lower confidence
        ],
        'sh': [
            # Highest confidence
            (re.compile(r'^\s*#!/bin/(bash|sh|zsh)'), 4), # Shebang is definitive
            (re.compile(r'\$\{\w+\}|\$\w+'), 3), # Variable expansion is ubiquitous
            (re.compile(r'\b(then|fi|done)\b'), 3), # Shell-specific block terminators
            # High confidence
            (re.compile(r'^\s*(if|for|while)\s+'), 2),
            (re.compile(r'\s\[\[?.*\s\]\]?'), 2), # Test conditions like `if [ -f ... ]`
            # Medium confidence
            (re.compile(r'^\s*echo\s+'), 1),
            (re.compile(r'^\s*export\s+\w+'), 1),
        ],
        'kt': [
            # Highest confidence patterns, very unique to Kotlin
            (re.compile(r'\bdata\s+class\b'), 4),  # `data class` is a highly specific Kotlin feature.
            (re.compile(r'\bfun\b\s+.*\)\s*:\s*\w+'), 4), # Catches the unique function return type syntax, e.g., `): String`.
            # High confidence patterns
            (re.compile(r'^\s*package\s+[\w\.]+'), 3), # Package declaration at the top of a file is common in Kotlin/Java.
            (re.compile(r'\bval\b\s+\w+\s*:'), 3), # `val` for constants is a very strong Kotlin signal (vs. Swift's `let`).
            (re.compile(r'\bfun\b\s+\w+\s*\('), 2), # The `fun` keyword itself is still a very strong indicator.
            (re.compile(r'\b(val|var)\s+\w+\s*='), 2), # Type-inferred val/var is common
            # Medium confidence patterns that add to the score
            (re.compile(r'\s\?\:|\s\!\!\s'), 2), # Null-safety operators: Elvis `?:` and not-null assertion `!!`.
            (re.compile(r'\b(companion\s+)?object\b'), 2), # `object` for singletons or companion objects is unique.
            (re.compile(r'\bvar\b\s+\w+\s*:\s*\w+'), 1) # `var` with a type is less unique but adds to the evidence.
        ],
        'cbl': [
            # IBM Mainframe specific (highest confidence)
            (re.compile(r'\bEXEC\s+(CICS|SQL)\b', re.IGNORECASE), 4),
            # Core COBOL Structure (very high confidence)
            (re.compile(r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\s*\.', re.IGNORECASE), 3),
            (re.compile(r'^\s*PROGRAM-ID\s*\.', re.IGNORECASE), 3),
            (re.compile(r'\bSELECT\s+[\w-]+\s+ASSIGN\s+TO\b', re.IGNORECASE), 3),
            # Common Sections and Clauses (high confidence)
            (re.compile(r'^\s*(WORKING-STORAGE|FILE)\s+SECTION\s*\.', re.IGNORECASE), 2),
            (re.compile(r'\s(PIC|PICTURE)\s+', re.IGNORECASE), 2),
            (re.compile(r'\bCOPY\s+[\w-]+\s*\.', re.IGNORECASE), 2),
            (re.compile(r'^\s*\d{2}\s+[\w-]+\s*\.', re.IGNORECASE), 2),
            # Common Verbs (medium confidence)
            (re.compile(r'\b(DISPLAY|MOVE|PERFORM|COMPUTE|EVALUATE|STOP\s+RUN)\b', re.IGNORECASE), 1),
        ],
        'swift': [
            # Core language keywords for declarations (highest confidence)
            (re.compile(r'\b(protocol|extension)\b\s+\w+'), 4),      # These are highly unique to Swift
            (re.compile(r'\b(func|struct|enum)\b\s+\w+'), 3),         # 'func' is a very strong signal
            # Function return type syntax (very high confidence)
            (re.compile(r'\)\s*->\s*\w+(?!\s*:)'), 3),
            # Common Apple framework imports (very high confidence)
            (re.compile(r'\bimport\b\s+(UIKit|SwiftUI|Foundation)\b'), 3),
            # Variable and constant declarations with type annotation (high confidence)
            (re.compile(r'\bclass\b\s+\w+\s*:'), 2), # Look for inheritance, a weaker but still good signal
            (re.compile(r'\b(let|var)\b\s+\w+\s*:'), 2),
            # Optional type syntax (high confidence)
            (re.compile(r':\s*\w+\?'), 2), # Optional type syntax (e.g., ": String?"), much more specific
            # Common property wrappers and attributes (high confidence)
            (re.compile(r'@(IBOutlet|IBAction|Published|State|main)\b'), 2),
        ],
        'sql': [
            # Highest confidence - combinations of keywords are almost exclusively SQL
            (re.compile(r'^\s*(SELECT\s+.*\s+FROM|CREATE\s+TABLE|INSERT\s+INTO|UPDATE\s+\w+\s+SET)\b', re.IGNORECASE), 4),
            (re.compile(r'^\s*(ALTER|DROP)\s+TABLE\b', re.IGNORECASE), 4),
            # High confidence - clauses that are very specific to SQL
            (re.compile(r'\b(INNER|LEFT|RIGHT|FULL)\s+(OUTER\s+)?JOIN\b', re.IGNORECASE), 3),
            (re.compile(r'\b(GROUP|ORDER)\s+BY\b', re.IGNORECASE), 3),
            # Medium confidence - common keywords and comments
            (re.compile(r'--.*'), 2), # SQL-style single-line comment
            (re.compile(r'^\s*(WHERE|VALUES|HAVING)\b', re.IGNORECASE), 2),
            # Low confidence - common data types that could appear elsewhere
            (re.compile(r'\b(VARCHAR|INT|DECIMAL|DATETIME|CHAR)\b', re.IGNORECASE), 1),
        ],
        'scala': [
            # Highest confidence - highly unique Scala syntax
            (re.compile(r'\bcase\s+class\b'), 4), # `case class` is very idiomatic
            (re.compile(r'\b(val|var)\s+\w+\s*:\s*\w+\[\w+\]'), 4), # Declaration with generic type, e.g., val x: List[String]
            # High confidence - very common and distinctive features
            (re.compile(r'\bdef\s+\w+\s*\(.*\)\s*:\s*\w+\s*='), 3), # Function definition with return type and `=`
            (re.compile(r'\bobject\b\s+\w+\s*(extends|\{)'), 3), # Singleton objects are a core feature
            (re.compile(r'\bimport\s+scala\._'), 3), # Common wildcard import
            # Medium confidence - strong indicators that might have some overlap
            (re.compile(r'\b(trait|implicit|sealed)\b'), 2), # Core Scala keywords
            (re.compile(r'\bcase\b\s+.*\s*=>'), 2), # Case in a match statement
            (re.compile(r'\b(List|Seq|Map|Option)\[\w+\]'), 2), # Use of [] for generics
            # Low confidence - functional patterns common in other languages too
            (re.compile(r'\.(map|filter|flatMap)\s*\{'), 1),
        ],
    }
    match_counts = {lang: 0 for lang in patterns}
    for lang, regex_list in patterns.items():
        for regex, weight in regex_list:
            if regex.search(script):
                match_counts[lang] += weight
    detected_language = max(match_counts, key=lambda k: match_counts[k])
    if match_counts[detected_language] == 0:
        return 'Unknown'
    return detected_language

# ==============================================================================
#  METHOD 2: PYGMENTS-BASED DETECTOR
# ==============================================================================

def detect_language_pygments(script: str) -> str:
    """Detects the programming language using the pygments library."""
    if not script or not script.strip():
        return 'Unknown'
    try:
        lexer = guess_lexer(script)
    except ClassNotFound:
        return 'Unknown'

    if not lexer.aliases or lexer.name == 'Text only':
        return 'Unknown'

    target_languages = {
        'cs', 'java', 'js', 'py', 'yaml', 'yml', 'sh', 'kt', 'cbl', 'swift', 'sql', 'scala'
    }
    for alias in lexer.aliases:
        if alias in target_languages:
            return alias
    return lexer.aliases[0]

# ==============================================================================
#  METHOD 3: WHATS-THAT-CODE-BASED DETECTOR
# ==============================================================================

def detect_language_whatsthatcode(script: str) -> str:
    """
    Detects the programming language using the whats-that-code library's
    election method, which combines multiple strategies for highest accuracy.
    """
    if not script or not script.strip():
        return 'Unknown'

    # The function returns a list of possible languages, ordered by confidence.
    # We don't have a filename, so we pass None or omit it.
    guess = guess_language_all_methods(script)

    if not guess:
        return 'Unknown'

    # Map the library's output (e.g., 'c-sharp') to the short aliases
    # used in the benchmark (e.g., 'cs') for a fair comparison.
    WTC_TO_ALIAS_MAP = {
        'c-sharp': 'cs',
        'shell': 'sh',
        'bash': 'sh',
        'kotlin': 'kt',
        'cobol': 'cbl',
        'python': 'py',
        'javascript': 'js',
        'yaml': 'yaml',
        'java': 'java',
        'sql': 'sql',
        'swift': 'swift',
        'scala': 'scala'
    }

    # Use the map to get the correct alias; fall back to the original
    # guess if it's not in our specific map.
    return WTC_TO_ALIAS_MAP.get(guess, guess)


# ==============================================================================
#  BENCHMARK DATA
# ==============================================================================

# Do not add single lines please they are hard for even humans to identify and not realistic usage
code_samples = [
    {'id': 1,'name': 'C#', 'expected': 'cs', 'code': "public class Game { public int Health { get; set; } }"},
    {'id': 2,'name': 'Python', 'expected': 'py', 'code': "import os\n\nif __name__ == '__main__':\n    print(f'Hello from {os.name}')"},
    {'id': 3,'name': 'Java', 'expected': 'java', 'code': "import java.util.ArrayList; \n public class Test { // ... }"},
    {'id': 4,'name': 'JavaScript', 'expected': 'js', 'code': "const greet = (name) => console.log(`Hello, ${name}!`);"},
    {'id': 5,'name': 'YAML', 'expected': 'yaml', 'code': "apiVersion: v1\nkind: Pod\nmetadata:\n  name: mypod"},
    {'id': 6,'name': 'Shell', 'expected': 'sh', 'code': "#!/bin/bash\nfor i in {1..5}; do\n  echo \"Welcome $i times\"\ndone"},
    {'id': 7,'name': 'Kotlin', 'expected': 'kt', 'code': "data class User(val name: String, val age: Int)"},
    {'id': 8,'name': 'Swift', 'expected': 'swift', 'code': "func greet(person: String) -> String {\n    return \"Hello, \\(person)!\"\n}"},
    {'id': 9,'name': 'Scala', 'expected': 'scala', 'code': "case class Person(name: String, age: Int)"},
    {'id': 10,'name': 'SQL', 'expected': 'sql', 'code': "SELECT user_id, user_name FROM users WHERE status = 'active' ORDER BY user_id;"},
    {'id': 11,'name': 'COBOL', 'expected': 'cbl', 'code': "IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\nPROCEDURE DIVISION.\nDISPLAY 'Hello world'.\nSTOP RUN."},
    {'id': 12,'name': 'Plain Text', 'expected': 'Unknown', 'code': "This is a sentence that is definitely not code."},
    {'id': 13,'name': 'Java2', 'expected': 'java', 'code': "public boolean checkIsAnyProductDeleted(Order order,DiscountOffer discountOffer) { boolean isAnyProductDeleted = false; boolean productDeletedOfferFlag = false; List<Long> productIds = new ArrayList<>(); List<OrderItem> deletedOrderItems = new ArrayList<>(); for (OrderItem orderItem : order.getOrderItemList()) { Long productId = orderItem.getShowcase().getProductId(); Boolean isProductDeleted = fafStoreDelegate.checkProductIsDeletedOrDisabled(productId); if (isProductDeleted) { productDeletedOfferFlag = checkIsAnyProductDeleted2(discountOffer, orderItem, productDeletedOfferFlag); deletedOrderItems.add(orderItem); productIds.add(orderItem.getShowcase().getProductId()); isAnyProductDeleted = true; } } if(productDeletedOfferFlag){ try{ Order newOrder = generateNewOrder(order,discountOffer); order.setStatus(OrderStatus.OFFER_CANCELED); discountOffer.setOfferStatus(OfferStatus.OUT_OF_STOCK); discountOffer.setIsIgnored(true); List<OrderItem> newOrderItemsDeleted = new ArrayList<>(); checkIsAnyProductClosedForSale3(newOrder, productIds, newOrderItemsDeleted); newOrder.getOrderItemList().removeAll(newOrderItemsDeleted); checkIsAnyProductDeleted3(newOrder); orderRepository.save(newOrder); orderRepository.save(order); discountOfferRepository.save(discountOffer); offerService.sendNotification(discountOffer.getOfferStatus(),discountOffer.getBuyerId(),discountOffer.getSellerId(),discountOffer); return isAnyProductDeleted; }catch ( Exception e ){ order.getOrderItemList().removeAll(deletedOrderItems); checkIsAnyProductDeleted4(deletedOrderItems); } }else{ order.getOrderItemList().removeAll(deletedOrderItems); for (OrderItem deletedOrderItem : deletedOrderItems) { deletedOrderItem.setDeleted(true); } } orderItemRepository.saveAll(deletedOrderItems); boolean isAllProductsRemovedFromBasket = false; checkIsAnyProductDeleted5(order, isAllProductsRemovedFromBasket); orderRepository.save(order); return isAnyProductDeleted; } private static void checkIsAnyProductDeleted5(Order order, boolean isAllProductsRemovedFromBasket) { if(CollectionUtils.isEmpty(order.getOrderItemList())){ isAllProductsRemovedFromBasket = true; } if ( isAllProductsRemovedFromBasket ) { order.setDeleted(true); }else{ order.calculateTotals(); } } private static void checkIsAnyProductDeleted4(List<OrderItem> deletedOrderItems) { for (OrderItem deletedOrderItem : deletedOrderItems ) { deletedOrderItem.setDeleted(true); } } private static void checkIsAnyProductDeleted3(Order newOrder) { if(CollectionUtils.isEmpty(newOrder.getOrderItemList())){ newOrder.setDeleted(true); } } private static boolean checkIsAnyProductDeleted2(DiscountOffer discountOffer, OrderItem orderItem, boolean productDeletedOfferFlag) { if(Objects.nonNull(discountOffer)){ productDeletedOfferFlag = true; }else{ orderItem.setDeleted(true); } return productDeletedOfferFlag; }"},
    {'id': 14,'name': 'C#2', 'expected': 'cs', 'code':"private string GetGitDiff() { try { var dte2 = (EnvDTE80.DTE2)ServiceProvider.GlobalProvider.GetService(typeof(EnvDTE.DTE)); string solutionName = dte2?.Solution?.FullName; if (solutionName == null) { throw new InvalidOperationException($\"Solution is not loaded or path is not available.\"); } var repositoryPath = Repository.Discover(solutionName); if (repositoryPath == null) { throw new InvalidOperationException(\"Repository path could not be discovered.\"); } using (var repo = new Repository(repositoryPath)) { var diff = repo.Diff.Compare<Patch>(repo.Head.Tip.Tree, DiffTargets.WorkingDirectory); return diff.Content; } } catch (Exception ex) { throw new Exception($\"Failed to get git diff (if you are not working on a VS solution please use another CodeMantis IDE extension): {ex.Message}\", ex); } }"},
    {'id': 15,'name': 'Python2', 'expected': 'py', 'code':"class User:\n    def __init__(self, name: str, age: int):\n        self.name = name\n        self.age = age\n\n    def greet(self) -> str:\n        return f'Hello, {self.name}!'\n\nif __name__ == '__main__':\n    user = User('Alice', 30)\n    print(user.greet())"},
    {'id': 16,'name': 'Python3', 'expected': 'py', 'code': "class User:\n    def __init__(self, name: str, age: int):\n        self.name = name\n        self.age = age\n\n    def greet(self) -> str:\n        return f'Hello, {self.name}!'\n\n    async def process_and_stream_completion(self, selected_code: str | list[dict[str,str]] | None , user_prompt: str | None, prompt_number: int | None, adapter_name: str | None, session_id:int, active_window: str | None, neighbour_windows: list | None, content_root: 'ContentRoot' | None) -> 'AsyncGenerator[str, None]':\n        pass\n\nif __name__ == '__main__':\n    user = User('Alice', 30)\n    print(user.greet())"},
    {'id': 17,'name': 'Java3', 'expected': 'java', 'code': 'public class Calculator { public int add(int a, int b) { var sum = a + b; return sum; } }'},
    {'id': 18,'name': 'C#3', 'expected': 'cs', 'code': 'Func<int, int> square = x => x * x;'},
    {'id': 19,'name': 'YAML', 'expected': 'yaml', 'code': 'self: { service: "my-app" }'},
]

# ==============================================================================
#  BENCHMARK EXECUTION
# ==============================================================================

if __name__ == '__main__':
    detectors = {
        "Custom Regex": detect_language_regex,
        "Pygments": detect_language_pygments,
        "WhatsThatCode": detect_language_whatsthatcode,
    }

    print("--- Accuracy Benchmark ---")
    header = f"| {'Language (Expected)':<22} | {'Custom Regex':<15} | {'Pygments':<15} | {'WhatsThatCode':<15} |"
    print(header)
    print("-" * len(header))

    for sample in code_samples:
        expected = sample['expected']
        name = sample['name']
        row = f"| {name:<12} ({expected:<8}) |"
        
        for detector_name, detector_func in detectors.items():
            result = detector_func(sample['code'])
            # Add a checkmark if correct, 'x' if incorrect
            status = "✅" if result == expected else "❌"
            row += f" {result:<12} {status} |"
        
        print(row)

    print("\n" + "="*80 + "\n")

    print("--- Performance Benchmark ---")
    N_RUNS = 10
    print(f"Running each detector {N_RUNS} times over the entire suite of {len(code_samples)} samples...")

    for name, func in detectors.items():
        # Use timeit to get a precise timing
        total_time = timeit.timeit(
            lambda: [func(sample['code']) for sample in code_samples],
            number=N_RUNS
        )
        avg_time_per_run_ms = (total_time / N_RUNS) * 1000
        avg_time_per_sample_us = (avg_time_per_run_ms / len(code_samples)) * 1000
        
        print(f"\nDetector: {name}")
        print(f"  Total time for {N_RUNS} runs: {total_time:.4f} seconds")
        print(f"  Average time per sample: {avg_time_per_sample_us:.2f} µs (microseconds)")