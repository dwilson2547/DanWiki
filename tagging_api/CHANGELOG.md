# Changelog

All notable changes to the Wiki Tagging Service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-21

### Added

- **Testing Framework**: Comprehensive test suite for evaluating tagging API performance
  - `test_suite.py`: Main test runner script with command-line interface
  - `test_cases.yaml`: YAML configuration for test cases and settings
  - 8 diverse test fixtures covering different content types:
    - Flask tutorial (programming/tutorial content)
    - Database troubleshooting (technical problem-solving)
    - React Hooks reference (API documentation)
    - Docker Compose guide (DevOps/infrastructure)
    - Machine Learning concepts (educational/conceptual)
    - Team onboarding (process/HR documentation)
    - API authentication (security-focused technical)
    - Marketing campaign report (business/analytics)
  - Automated testing across all 4 prompt templates (detailed, quick, technical, general)
  - Comprehensive markdown report generation with side-by-side template comparisons
  - Raw JSON output for detailed analysis
  - Performance metrics tracking (processing time, token count, tag statistics)
  - Real-time console progress indicators

- **Testing Documentation**:
  - `TESTING_QUICKSTART.md`: Quick start guide for running tests
  - `TEST_SUITE_README.md`: Complete testing framework documentation
  - `TESTING_SUMMARY.md`: Implementation overview and benefits
  - `EXAMPLE_OUTPUT.md`: Sample outputs and evaluation guidance

- **Version Tracking**: Added CHANGELOG.md to track service changes

### Changed

- Updated `requirements.txt` to include optional testing dependencies (requests, pyyaml)
- Service version bumped to 1.1.0

## [1.0.0] - Initial Release

### Added

- Core tagging API service with FastAPI
- LLM-based tag generation using local models
- Support for multiple prompt templates:
  - `detailed`: Comprehensive analysis
  - `quick`: Fast processing
  - `technical`: Code-focused
  - `general`: Balanced approach
- Synchronous `/analyze` endpoint for single-page tagging
- Asynchronous `/analyze/batch` endpoint for batch processing
- Redis Queue (RQ) integration for background job processing
- Semantic tag matching using sentence-transformers
- GPU acceleration support with 4-bit/8-bit quantization
- Configurable generation parameters (temperature, top_p, max_tokens)
- Health check and service info endpoints
- Comprehensive configuration via environment variables
- Worker process for batch job execution
- Authentication via bearer tokens
- CORS support for web clients
