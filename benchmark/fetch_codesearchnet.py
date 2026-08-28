import datasets
import json
import warnings
warnings.filterwarnings("ignore")

LANGS = {
    "go": "go", "java": "java", "javascript": "js",
    "php": "php", "python": "py", "ruby": "rb",
}

N_PER_LANG = 300
OUT_PATH = r"C:\Repos\language-dataset\codesearchnet_samples.jsonl"

samples = []
for hf_lang, code in LANGS.items():
    ds = datasets.load_dataset("code-search-net/code_search_net", hf_lang, split="test", streaming=True)
    n = 0
    for row in ds:
        content = row["whole_func_string"]
        if not content or not content.strip():
            continue
        samples.append({"lang": code, "content": content})
        n += 1
        if n >= N_PER_LANG:
            break
    print(f"{hf_lang}: {n} samples")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print(f"Total: {len(samples)} -> {OUT_PATH}")
