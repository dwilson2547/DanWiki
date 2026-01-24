# Tagging API Test Suite

Comprehensive testing framework for evaluating tagging API performance across multiple prompt templates.

## Overview

This test suite allows you to:
- Run batch tests with diverse content types
- Compare output across different prompt templates
- Generate detailed reports for manual evaluation
- Save raw JSON outputs for further analysis

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies (if not already installed)
pip install requests pyyaml
```

### 2. Configure API Token

```bash
# Set your API token
export TAGGING_API_TOKEN="your-token-here"

# Or add to your .env file
echo "TAGGING_API_TOKEN=your-token-here" >> .env
```

### 3. Ensure Tagging API is Running

```bash
# Start the tagging API (in another terminal)
cd tagging_api
uvicorn app:app --reload --port 8002
```

### 4. Run Tests

```bash
# Run all tests with all prompt templates
python test_suite.py

# Test specific templates only
python test_suite.py --templates detailed,quick

# Use custom config file
python test_suite.py --config my_tests.yaml

# Override API URL
python test_suite.py --api-url http://localhost:8003
```

## Project Structure

```
tagging_api/
├── test_suite.py          # Main test runner script
├── test_cases.yaml        # Test configuration
├── test_fixtures/         # Sample content files
│   ├── flask_tutorial.md
│   ├── database_troubleshooting.md
│   ├── react_hooks_reference.md
│   ├── docker_compose_guide.md
│   ├── machine_learning_concepts.md
│   ├── team_onboarding.md
│   ├── api_authentication.md
│   └── marketing_report.md
└── test_results/          # Generated test results
    └── YYYYMMDD_HHMMSS/   # Timestamped run
        ├── raw_results.json
        └── report.md
```

## Test Configuration

Edit `test_cases.yaml` to customize tests:

### Adding New Test Cases

```yaml
test_cases:
  - name: "My New Test"
    fixture: "my_content.md"
    title: "Page Title"
    existing_tags:
      - name: "python"
        color: "#3776AB"
    context:
      breadcrumbs:
        - "Category"
        - "Subcategory"
      wiki_name: "My Wiki"
    description: "What this test evaluates"
    expected_tag_categories:
      - "expected-tag-1"
      - "expected-tag-2"
```

### Test Configuration Options

```yaml
test_config:
  api_url: "http://localhost:8002"
  api_token_env: "TAGGING_API_TOKEN"
  max_tags: 10
  min_confidence: 0.5
  prompt_templates: []  # Empty = test all
  save_raw_json: true
  generate_markdown_report: true
  request_timeout: 60
  delay_between_requests: 0.5
```

## Available Test Fixtures

The test suite includes 8 diverse content types:

1. **flask_tutorial.md** - Beginner programming tutorial
2. **database_troubleshooting.md** - Technical troubleshooting guide
3. **react_hooks_reference.md** - API reference documentation
4. **docker_compose_guide.md** - DevOps/infrastructure guide
5. **machine_learning_concepts.md** - Educational/conceptual content
6. **team_onboarding.md** - Process/HR documentation
7. **api_authentication.md** - Security-focused technical content
8. **marketing_report.md** - Business/analytics report

## Understanding Results

### Console Output

```
🚀 Starting Test Suite
   Test cases: 8
   Prompt templates: detailed, quick, technical, general
   Total tests: 32

📋 Test Case: Flask Tutorial
    ✅ detailed      - 8 tags
    ✅ quick         - 6 tags
    ✅ technical     - 9 tags
    ✅ general       - 7 tags
```

### Raw Results (`raw_results.json`)

Complete JSON output from all API calls including:
- All generated tags with confidence scores
- Processing times
- Statistics (new vs. existing tags)
- Error messages (if any)

### Markdown Report (`report.md`)

Comprehensive human-readable report with:
- Summary statistics
- Detailed results for each test case
- Tag comparison tables across templates
- Performance metrics

## Evaluating Results

### What to Look For

1. **Tag Relevance**: Do tags accurately describe the content?
2. **Consistency**: Similar results across templates for the same content?
3. **Diversity**: Different templates capturing different aspects?
4. **Confidence Scores**: Are they reasonable and well-calibrated?
5. **New vs. Existing**: Appropriate balance of suggesting new tags vs. matching existing ones?

### Comparing Templates

The report includes comparison tables showing which tags each template suggested:

```markdown
| Tag | detailed | quick | technical | general |
|-----|----------|-------|-----------|---------|
| python | 0.92 | 0.88 | 0.95 | 0.90 |
| tutorial | 0.85 | - | 0.78 | 0.82 |
| flask | 0.95 | 0.92 | 0.96 | 0.93 |
```

This helps identify:
- Which templates are more aggressive (suggest more tags)
- Which templates are more conservative
- Template-specific biases or patterns

## Adding Custom Test Cases

### 1. Create Content Fixture

```bash
# Create new fixture file
cat > test_fixtures/my_content.md << 'EOF'
# My Content Title

Your markdown content here...
EOF
```

### 2. Add to test_cases.yaml

```yaml
test_cases:
  - name: "My Custom Test"
    fixture: "my_content.md"
    title: "My Content Title"
    existing_tags: []
    context:
      breadcrumbs: ["Category"]
    description: "Description of what this tests"
```

### 3. Run Tests

```bash
python test_suite.py
```

## Advanced Usage

### Testing Custom Prompt Templates

If you add new prompt templates to `prompts/`, test them:

```bash
python test_suite.py --templates my_new_template,detailed
```

### Automated Testing in CI/CD

```bash
# In your CI pipeline
export TAGGING_API_TOKEN="${CI_API_TOKEN}"
python test_suite.py --api-url http://tagging-api:8002

# Check for failures
if [ $? -ne 0 ]; then
    echo "Tagging API tests failed"
    exit 1
fi
```

### Batch Testing Different Configurations

```bash
# Test different confidence thresholds
for conf in 0.3 0.5 0.7; do
    # Update config programmatically
    python test_suite.py --config "config_conf_${conf}.yaml"
done
```

## Troubleshooting

### API Token Issues

```
⚠️  Warning: TAGGING_API_TOKEN environment variable not set
```

**Solution:**
```bash
export TAGGING_API_TOKEN="your-token-here"
```

### Connection Errors

```
❌ Error: Connection refused
```

**Solution:** Ensure tagging API is running:
```bash
uvicorn app:app --port 8002
```

### Timeout Errors

**Solution:** Increase timeout in `test_cases.yaml`:
```yaml
test_config:
  request_timeout: 120  # Increase to 2 minutes
```

### Missing Fixtures

```
❌ Error: Fixture not found: my_file.md
```

**Solution:** Ensure fixture file exists in `test_fixtures/` directory.

## Performance Considerations

- **Delay Between Requests**: Prevents overwhelming the API
- **Request Timeout**: Adjust based on model size and GPU speed
- **Batch Size**: Test suite runs sequentially (no parallel requests)

## Future Enhancements

Potential additions:
- HTML report generation with visualizations
- Automated quality scoring
- Regression testing (compare against baseline)
- A/B testing different model configurations
- Integration with MLflow or similar tracking tools

## Questions?

See the main [Tagging API Documentation](README_QUICK.md) or reach out to the team.
