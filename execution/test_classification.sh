#!/bin/bash
# test_classification.sh — classifies 5 hardcoded test posts and prints PASS/FAIL per case.
# Run from any directory; script resolves paths relative to itself.
set -e
cd "$(dirname "$0")/.."
cd backend
source .venv/bin/activate 2>/dev/null || true
python -c "
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.llm.classifier import LLMClassifier
from src.db.repositories.product_repository import ProductRepository

product = ProductRepository().get_by_slug('wealthsimple-trade')
if product is None:
    print('ERROR: product wealthsimple-trade not found in DB. Run execution/init_db.sh first.')
    sys.exit(1)

classifier = LLMClassifier()

tests = [
    ('app crashed when I opened options chain', 'bug_report'),
    ('wish they had fractional shares for ETFs', 'feature_request'),
    ('love the new UI update', 'praise'),
    ('Phil Spencer stepping down as Xbox CEO', 'general_discussion'),
    ('spreads are confusing to display', 'complaint'),
]

passed = 0
for content, expected in tests:
    result = classifier.classify({'content': content}, product)
    got = result.get('category', 'NONE')
    provider = result.get('llm_provider', 'unknown')
    status_flag = 'PASS' if got == expected else 'FAIL'
    if got == expected:
        passed += 1
    print(f'[{status_flag}] expected={expected} got={got} provider={provider} confidence={result.get(\"confidence\", 0):.2f}')
    print(f'       summary: {result.get(\"summary\", \"\")}')
    print(f'       topics:  {result.get(\"topics\", [])}')
    print()

print(f'Result: {passed}/{len(tests)} passed')
sys.exit(0 if passed >= 4 else 1)
"
