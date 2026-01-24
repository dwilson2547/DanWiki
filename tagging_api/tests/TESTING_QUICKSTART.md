# Quick Start: Testing the Tagging API

## Prerequisites

```bash
# Install test dependencies
pip install requests pyyaml

# Set API token
export TAGGING_API_TOKEN="your-secret-token-here"
```

## Start the Tagging API

```bash
cd tagging_api
uvicorn app:app --reload --port 8002
```

## Run Tests

```bash
# Run all tests
python test_suite.py

# This will:
# - Test 8 different content types
# - Run each through 4 prompt templates (detailed, quick, technical, general)
# - Generate results in test_results/YYYYMMDD_HHMMSS/
```

## View Results

```bash
# Open the markdown report
cd test_results/
ls -lt  # Find latest run
cd YYYYMMDD_HHMMSS/
cat report.md  # Or open in your favorite markdown viewer
```

## What's Included

- **8 diverse test fixtures** covering different content types
- **4 prompt templates** for comparison
- **Detailed reports** showing tag suggestions, confidence scores, and performance
- **Side-by-side comparisons** of template outputs

## Next Steps

1. Review the generated `report.md` to evaluate tag quality
2. Adjust prompt templates in `prompts/` based on findings
3. Add your own test cases in `test_cases.yaml`
4. Create custom fixtures in `test_fixtures/`

See [TEST_SUITE_README.md](TEST_SUITE_README.md) for complete documentation.
