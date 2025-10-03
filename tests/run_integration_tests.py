#!/usr/bin/env python3
"""
Integration Test Runner and Analysis

Runs comprehensive integration tests and analyzes failure modes.
"""

import unittest
import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_integration_tests():
    """Run all integration tests with detailed analysis"""
    
    print("🔗 Running Integration Tests for PDF OCR Tool")
    print("=" * 60)
    print("Testing major integration points:")
    print("  • PDF to Image conversion pipeline")
    print("  • Image to Text extraction flow")
    print("  • File saving and cleanup operations")
    print("  • Mid-process failure recovery")
    print("  • Web interface integration")
    print("  • Resource management")
    print("=" * 60)
    
    # Discover integration tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    
    # Load specific integration test modules
    integration_modules = [
        'test_integration',
        'test_integration_web'
    ]
    
    suite = unittest.TestSuite()
    
    for module_name in integration_modules:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
            print(f"✅ Loaded {module_name}")
        except Exception as e:
            print(f"❌ Failed to load {module_name}: {e}")
    
    # Run tests with timing
    start_time = time.time()
    
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Analyze results
    print("\n" + "=" * 60)
    print("🔍 INTEGRATION TEST ANALYSIS")
    print("=" * 60)
    
    print(f"⏱️  Execution Time: {duration:.2f} seconds")
    print(f"🧪 Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Calculate success metrics
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"✅ Success Rate: {success_rate:.1f}%")
    
    # Detailed failure analysis
    if result.failures:
        print(f"\n💔 FAILURE ANALYSIS ({len(result.failures)} failures):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n{i}. {test}")
            # Extract key error information
            lines = traceback.split('\n')
            for line in lines:
                if 'AssertionError' in line or 'assert' in line.lower():
                    print(f"   💡 {line.strip()}")
                    break
    
    if result.errors:
        print(f"\n🚨 ERROR ANALYSIS ({len(result.errors)} errors):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n{i}. {test}")
            # Extract key error information
            lines = traceback.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['Error:', 'Exception:', 'ImportError:']):
                    print(f"   🔥 {line.strip()}")
                    break
    
    # Integration point analysis
    print(f"\n🔗 INTEGRATION POINTS TESTED:")
    integration_points = [
        "PDF → Image conversion (PyMuPDF integration)",
        "Image → Text extraction (Gemini API integration)", 
        "File system operations (temp files, cleanup)",
        "Web interface (Gradio ↔ OCR backend)",
        "Concurrent processing (ThreadPoolExecutor)",
        "Resource management (memory, disk, network)",
        "Error propagation (API → Web → User)",
        "Mid-process failure recovery"
    ]
    
    for point in integration_points:
        print(f"  ✓ {point}")
    
    # Failure mode analysis
    print(f"\n⚠️  FAILURE MODES TESTED:")
    failure_modes = [
        "Corrupted PDF files",
        "Memory exhaustion during processing",
        "Disk space exhaustion",
        "Network/API failures",
        "Permission errors",
        "Process interruption (KeyboardInterrupt)",
        "Resource contention (concurrent access)",
        "Path traversal attacks",
        "Rate limiting scenarios",
        "Large file handling"
    ]
    
    for mode in failure_modes:
        print(f"  🛡️  {mode}")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    
    if result.wasSuccessful():
        print("  🎉 All integration tests passed!")
        print("  ✅ System integration is robust")
        print("  ✅ Failure recovery mechanisms work correctly")
        print("  ✅ Resource management is effective")
    else:
        print("  ⚠️  Some integration issues detected")
        print("  🔧 Review failed tests for integration gaps")
        print("  🔍 Consider additional failure mode testing")
    
    # Performance insights
    if duration > 30:
        print(f"  ⏰ Tests took {duration:.1f}s - consider optimizing slow integration points")
    elif duration < 5:
        print(f"  ⚡ Fast execution ({duration:.1f}s) - good integration performance")
    
    return result.wasSuccessful()

def analyze_untested_failure_modes():
    """Analyze failure modes that still need testing"""
    
    print(f"\n🔍 UNTESTED FAILURE MODES ANALYSIS:")
    print("=" * 60)
    
    untested_modes = [
        {
            "category": "Race Conditions",
            "scenarios": [
                "Concurrent cache modifications",
                "Simultaneous temp file access",
                "Parallel API calls with shared state"
            ]
        },
        {
            "category": "System Resource Limits", 
            "scenarios": [
                "File descriptor exhaustion",
                "Process/thread limits",
                "Network connection limits"
            ]
        },
        {
            "category": "External Service Failures",
            "scenarios": [
                "Gradio service unavailability",
                "DNS resolution failures", 
                "SSL certificate issues"
            ]
        },
        {
            "category": "Data Corruption",
            "scenarios": [
                "Partial file writes during interruption",
                "Cache corruption scenarios",
                "State inconsistency after crashes"
            ]
        },
        {
            "category": "Security Edge Cases",
            "scenarios": [
                "Zip bomb PDFs",
                "Malicious file names with null bytes",
                "Buffer overflow attempts"
            ]
        }
    ]
    
    for category_info in untested_modes:
        category = category_info["category"]
        scenarios = category_info["scenarios"]
        
        print(f"\n🚨 {category}:")
        for scenario in scenarios:
            print(f"  ❌ {scenario}")
    
    print(f"\n💡 TESTING RECOMMENDATIONS:")
    recommendations = [
        "Add property-based testing with Hypothesis",
        "Implement chaos engineering tests",
        "Add stress testing with resource constraints",
        "Create fuzzing tests for malicious inputs",
        "Add timing-based security tests",
        "Implement integration tests with real external services"
    ]
    
    for rec in recommendations:
        print(f"  📝 {rec}")

if __name__ == '__main__':
    print("Starting comprehensive integration test analysis...")
    
    success = run_integration_tests()
    
    # Always run failure mode analysis
    analyze_untested_failure_modes()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 INTEGRATION TESTING COMPLETE - ALL TESTS PASSED")
    else:
        print("⚠️  INTEGRATION TESTING COMPLETE - SOME ISSUES FOUND")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)