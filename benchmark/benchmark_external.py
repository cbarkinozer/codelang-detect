"""External benchmark: smola/language-dataset (github.com/smola/language-dataset).

Independent, real-world-GitHub, human-reviewed programming-language-ID dataset.
Restricted to the language set codelang-detect actually supports (fair comparison).
"""
from collections import defaultdict
import os
import sys
import json
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark import detect_pygments, detect_whatsthatcode, detect_codelang, PYGMENTS_INSTALLED, WTC_INSTALLED

DATASET_NAME = os.environ.get("DATASET_NAME", "smola/language-dataset")
SAMPLES_PATH = os.environ.get("SAMPLES_PATH", r"C:\Repos\language-dataset\samples.jsonl")


def load_samples():
    samples = []
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples


def macro_f1(samples, predictions, labels):
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    for s, pred in zip(samples, predictions):
        gold = s["lang"]
        if pred == gold:
            tp[gold] += 1
        else:
            fp[pred] += 1
            fn[gold] += 1
    f1s = []
    for lbl in labels:
        p = tp[lbl] / (tp[lbl] + fp[lbl]) if (tp[lbl] + fp[lbl]) else 0.0
        r = tp[lbl] / (tp[lbl] + fn[lbl]) if (tp[lbl] + fn[lbl]) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def main():
    samples = load_samples()
    labels = sorted(set(s["lang"] for s in samples))
    print(f"Loaded {len(samples)} labeled samples across {len(labels)} languages from {DATASET_NAME}\n")

    detectors = {
        "codelang-detect (ours)": detect_codelang,
        "Pygments": detect_pygments if PYGMENTS_INSTALLED else None,
        "WhatsThatCode": detect_whatsthatcode if WTC_INSTALLED else None,
    }

    print(f"{'Library':<25} {'Accuracy':>10} {'Macro-F1':>10} {'us/sample':>12}")
    print("-" * 60)

    results = {}
    for name, func in detectors.items():
        if func is None:
            print(f"{name:<25} {'not installed':>10}")
            continue

        predictions = []
        start = time.perf_counter()
        for s in samples:
            predictions.append(func(s["content"]))
        elapsed = time.perf_counter() - start

        correct = sum(1 for p, s in zip(predictions, samples) if p == s["lang"])
        acc = correct / len(samples) * 100
        f1 = macro_f1(samples, predictions, labels)
        us_per_sample = elapsed / len(samples) * 1_000_000

        print(f"{name:<25} {acc:>9.1f}% {f1:>10.3f} {us_per_sample:>10.1f}us")
        results[name] = {"accuracy": acc, "macro_f1": f1, "us_per_sample": us_per_sample,
                          "predictions": predictions}

    # Per-language breakdown for our detector
    print("\n--- Per-language accuracy: codelang-detect (ours) ---")
    per_lang_total = defaultdict(int)
    per_lang_correct = defaultdict(int)
    for s, p in zip(samples, results["codelang-detect (ours)"]["predictions"]):
        per_lang_total[s["lang"]] += 1
        if p == s["lang"]:
            per_lang_correct[s["lang"]] += 1
    for lbl in labels:
        t = per_lang_total[lbl]
        c = per_lang_correct[lbl]
        print(f"  {lbl:<8} {c:>3}/{t:<3} ({c/t*100:5.1f}%)")


if __name__ == "__main__":
    main()
