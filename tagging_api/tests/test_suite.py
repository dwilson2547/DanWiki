#!/usr/bin/env python3
"""
Test Suite for Tagging API

Runs a collection of test cases through the tagging API with multiple prompt templates
and generates comprehensive reports for evaluation.

Usage:
    python test_suite.py [--config test_cases.yaml] [--templates detailed,quick]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

import requests
import yaml


class TaggingAPITestSuite:
    """Test suite runner for tagging API."""
    
    def __init__(self, config_file: str = "test_cases.yaml"):
        """Initialize test suite with configuration."""
        self.config_file = config_file
        self.config = self._load_config()
        self.test_config = self.config.get('test_config', {})
        self.test_cases = self.config.get('test_cases', [])
        
        # API configuration
        self.api_url = self.test_config.get('api_url', 'http://localhost:8002')
        api_token_env = self.test_config.get('api_token_env', 'TAGGING_API_TOKEN')
        self.api_token = os.environ.get(api_token_env)
        
        if not self.api_token:
            print(f"⚠️  Warning: {api_token_env} environment variable not set")
            print("   The API may reject requests without authentication")
        
        # Test options
        self.max_tags = self.test_config.get('max_tags', 10)
        self.min_confidence = self.test_config.get('min_confidence', 0.5)
        self.request_timeout = self.test_config.get('request_timeout', 60)
        self.delay = self.test_config.get('delay_between_requests', 0.5)
        
        # Prompt templates to test
        self.prompt_templates = self.test_config.get('prompt_templates', [])
        if not self.prompt_templates:
            self.prompt_templates = ['detailed', 'quick', 'technical', 'general']
        
        # Results storage
        self.results: List[Dict[str, Any]] = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create output directory (in parent tagging_api directory)
        script_dir = Path(__file__).parent
        self.output_dir = script_dir.parent / 'test_results' / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict:
        """Load test configuration from YAML file."""
        config_path = Path(self.config_file)
        if not config_path.exists():
            print(f"❌ Configuration file not found: {self.config_file}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_fixture(self, fixture_name: str) -> str:
        """Load content from fixture file."""
        # Path relative to this script's location
        script_dir = Path(__file__).parent
        fixture_path = script_dir / 'test_fixtures' / fixture_name
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_name}")
        
        with open(fixture_path, 'r') as f:
            return f.read()
    
    def _call_api(self, 
                  title: str,
                  content: str,
                  existing_tags: List[Dict],
                  context: Optional[Dict],
                  prompt_template: str) -> Dict[str, Any]:
        """Call the tagging API analyze endpoint."""
        url = f"{self.api_url}/analyze"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        payload = {
            'title': title,
            'content': content,
            'existing_tags': existing_tags,
            'context': context,
            'options': {
                'max_tags': self.max_tags,
                'min_confidence': self.min_confidence,
                'prompt_template': prompt_template
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def run_test_case(self, test_case: Dict, prompt_template: str) -> Dict[str, Any]:
        """Run a single test case with specified prompt template."""
        print(f"  📝 Testing: {test_case['name']} with '{prompt_template}' template...")
        
        # Load fixture content
        try:
            content = self._load_fixture(test_case['fixture'])
        except FileNotFoundError as e:
            return {
                'test_case': test_case['name'],
                'prompt_template': prompt_template,
                'success': False,
                'error': str(e)
            }
        
        # Call API
        result = self._call_api(
            title=test_case['title'],
            content=content,
            existing_tags=test_case.get('existing_tags', []),
            context=test_case.get('context'),
            prompt_template=prompt_template
        )
        
        # Add metadata
        result['test_case'] = test_case['name']
        result['prompt_template'] = prompt_template
        result['fixture'] = test_case['fixture']
        result['title'] = test_case['title']
        result['description'] = test_case.get('description', '')
        result['expected_categories'] = test_case.get('expected_tag_categories', [])
        result['timestamp'] = datetime.now().isoformat()
        
        return result
    
    def run_all_tests(self, selected_templates: Optional[List[str]] = None):
        """Run all test cases with all prompt templates."""
        templates = selected_templates if selected_templates else self.prompt_templates
        
        print(f"\n🚀 Starting Test Suite")
        print(f"   Test cases: {len(self.test_cases)}")
        print(f"   Prompt templates: {', '.join(templates)}")
        print(f"   Total tests: {len(self.test_cases) * len(templates)}")
        print(f"   Output directory: {self.output_dir}\n")
        
        total_tests = len(self.test_cases) * len(templates)
        current_test = 0
        
        for test_case in self.test_cases:
            print(f"\n📋 Test Case: {test_case['name']}")
            
            for template in templates:
                current_test += 1
                result = self.run_test_case(test_case, template)
                self.results.append(result)
                
                # Status indicator
                status = "✅" if result.get('success') else "❌"
                tag_count = len(result.get('data', {}).get('tags', [])) if result.get('success') else 0
                print(f"    {status} {template:12s} - {tag_count} tags")
                
                # Rate limiting
                if current_test < total_tests:
                    time.sleep(self.delay)
        
        print(f"\n✨ All tests completed!\n")
    
    def save_raw_results(self):
        """Save raw JSON results."""
        if not self.test_config.get('save_raw_json', True):
            return
        
        output_file = self.output_dir / 'raw_results.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Raw results saved: {output_file}")
    
    def generate_markdown_report(self):
        """Generate comprehensive markdown report."""
        if not self.test_config.get('generate_markdown_report', True):
            return
        
        output_file = self.output_dir / 'report.md'
        
        with open(output_file, 'w') as f:
            # Header
            f.write(f"# Tagging API Test Results\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**API Endpoint:** {self.api_url}\n\n")
            
            # Summary statistics
            total = len(self.results)
            successful = sum(1 for r in self.results if r.get('success'))
            failed = total - successful
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tests:** {total}\n")
            f.write(f"- **Successful:** {successful} ({100*successful/total:.1f}%)\n")
            f.write(f"- **Failed:** {failed}\n")
            f.write(f"- **Test Cases:** {len(self.test_cases)}\n")
            f.write(f"- **Prompt Templates:** {', '.join(self.prompt_templates)}\n\n")
            
            # Group results by test case
            test_case_results = {}
            for result in self.results:
                test_case_name = result['test_case']
                if test_case_name not in test_case_results:
                    test_case_results[test_case_name] = []
                test_case_results[test_case_name].append(result)
            
            # Detailed results for each test case
            f.write(f"## Test Results by Case\n\n")
            
            for test_case_name, results in test_case_results.items():
                f.write(f"### {test_case_name}\n\n")
                
                # Get metadata from first result
                first_result = results[0]
                f.write(f"**Title:** {first_result['title']}\n\n")
                f.write(f"**Description:** {first_result['description']}\n\n")
                f.write(f"**Fixture:** `{first_result['fixture']}`\n\n")
                
                if first_result.get('expected_categories'):
                    f.write(f"**Expected Tag Categories:** {', '.join(first_result['expected_categories'])}\n\n")
                
                # Results by template
                for result in results:
                    template = result['prompt_template']
                    f.write(f"#### Prompt Template: `{template}`\n\n")
                    
                    if not result.get('success'):
                        f.write(f"❌ **Error:** {result.get('error', 'Unknown error')}\n\n")
                        continue
                    
                    data = result['data']
                    tags = data.get('tags', [])
                    stats = data.get('stats', {})
                    
                    # Statistics
                    f.write(f"**Performance:**\n")
                    f.write(f"- Processing time: {data.get('processing_time_ms', 0):.0f} ms\n")
                    f.write(f"- Tags generated: {len(tags)}\n")
                    f.write(f"- New tags: {stats.get('new_tags_suggested', 0)}\n")
                    f.write(f"- Existing tags matched: {stats.get('existing_tags_matched', 0)}\n")
                    f.write(f"- Content tokens: {stats.get('content_tokens', 0)}\n\n")
                    
                    # Tags table
                    if tags:
                        f.write("**Generated Tags:**\n\n")
                        f.write("| Tag | Confidence | New? | Category | Rationale |\n")
                        f.write("|-----|------------|------|----------|----------|\n")
                        
                        for tag in tags:
                            is_new = "✨" if tag.get('is_new') else "🔗"
                            matched = f" (→ {tag.get('matched_existing_tag')})" if tag.get('matched_existing_tag') else ""
                            category = tag.get('category', 'N/A')
                            rationale = tag.get('rationale', 'N/A')[:50]  # Truncate
                            
                            f.write(f"| {tag['name']}{matched} | {tag['confidence']:.2f} | {is_new} | {category} | {rationale}... |\n")
                        
                        f.write("\n")
                    else:
                        f.write("*No tags generated*\n\n")
                    
                    f.write("---\n\n")
            
            # Comparison across templates
            f.write(f"## Template Comparison\n\n")
            
            for test_case_name, results in test_case_results.items():
                f.write(f"### {test_case_name}\n\n")
                
                # Create comparison table
                all_tags = set()
                template_tags = {}
                
                for result in results:
                    if result.get('success'):
                        template = result['prompt_template']
                        tags = result['data'].get('tags', [])
                        template_tags[template] = {tag['name']: tag['confidence'] for tag in tags}
                        all_tags.update(tag['name'] for tag in tags)
                
                if all_tags:
                    f.write("| Tag | " + " | ".join(self.prompt_templates) + " |\n")
                    f.write("|-----|" + "|".join(["---"] * len(self.prompt_templates)) + "|\n")
                    
                    for tag in sorted(all_tags):
                        row = [tag]
                        for template in self.prompt_templates:
                            conf = template_tags.get(template, {}).get(tag)
                            row.append(f"{conf:.2f}" if conf else "-")
                        f.write("| " + " | ".join(row) + " |\n")
                    
                    f.write("\n")
                else:
                    f.write("*No tags to compare*\n\n")
            
            # Footer
            f.write(f"\n---\n\n")
            f.write(f"*Report generated by Tagging API Test Suite*\n")
        
        print(f"📊 Markdown report saved: {output_file}")
    
    def print_summary(self):
        """Print summary statistics to console."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('success'))
        
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests:      {total}")
        print(f"Successful:       {successful} ({100*successful/total:.1f}%)")
        print(f"Failed:           {total - successful}")
        print(f"Test cases:       {len(self.test_cases)}")
        print(f"Templates:        {', '.join(self.prompt_templates)}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test suite for Tagging API',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--config',
        default='test_cases.yaml',
        help='Path to test configuration YAML file (default: test_cases.yaml)'
    )
    parser.add_argument(
        '--templates',
        help='Comma-separated list of prompt templates to test (default: all)'
    )
    parser.add_argument(
        '--api-url',
        help='Override API URL from config'
    )
    
    args = parser.parse_args()
    
    # Initialize test suite
    suite = TaggingAPITestSuite(config_file=args.config)
    
    # Override API URL if provided
    if args.api_url:
        suite.api_url = args.api_url
    
    # Parse templates if provided
    selected_templates = None
    if args.templates:
        selected_templates = [t.strip() for t in args.templates.split(',')]
    
    # Run tests
    try:
        suite.run_all_tests(selected_templates)
        suite.save_raw_results()
        suite.generate_markdown_report()
        suite.print_summary()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
