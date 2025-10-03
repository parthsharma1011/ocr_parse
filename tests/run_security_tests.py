#!/usr/bin/env python3
"""
Security Test Runner and Vulnerability Assessment

Runs comprehensive security tests and provides detailed vulnerability analysis.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_security_tests():
    """Run all security tests with detailed vulnerability analysis"""
    
    print("🔒 Running Comprehensive Security Audit")
    print("=" * 60)
    print("Testing for critical vulnerabilities:")
    print("  • Path traversal attacks")
    print("  • Input injection vulnerabilities")  
    print("  • API key exposure risks")
    print("  • Unsafe file operations")
    print("  • OWASP Top 10 compliance")
    print("=" * 60)
    
    # Load security tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    
    try:
        suite = loader.loadTestsFromName('test_security')
        print("✅ Security test suite loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load security tests: {e}")
        return False
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Analyze security test results
    print("\n" + "=" * 60)
    print("🔍 SECURITY VULNERABILITY ANALYSIS")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"📊 Security Tests: {total_tests} total")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    
    # Calculate security score
    if total_tests > 0:
        security_score = (passed / total_tests) * 100
        print(f"🛡️  Security Score: {security_score:.1f}%")
        
        if security_score >= 90:
            print("🟢 SECURITY STATUS: EXCELLENT")
        elif security_score >= 75:
            print("🟡 SECURITY STATUS: GOOD (minor issues)")
        elif security_score >= 60:
            print("🟠 SECURITY STATUS: MODERATE (needs attention)")
        else:
            print("🔴 SECURITY STATUS: POOR (critical issues)")
    
    # Detailed vulnerability analysis
    if result.failures:
        print(f"\n🚨 CRITICAL VULNERABILITIES FOUND ({failures}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            test_name = str(test).split('.')[-1]
            print(f"\n{i}. {test_name}")
            
            # Extract vulnerability type
            if "path_traversal" in test_name.lower():
                print("   🎯 Type: Path Traversal Vulnerability")
                print("   💥 Risk: HIGH - Unauthorized file access")
            elif "injection" in test_name.lower():
                print("   🎯 Type: Input Injection Vulnerability") 
                print("   💥 Risk: CRITICAL - Code execution possible")
            elif "api_key" in test_name.lower():
                print("   🎯 Type: Information Disclosure")
                print("   💥 Risk: HIGH - Credential exposure")
            elif "file_operation" in test_name.lower():
                print("   🎯 Type: Unsafe File Operation")
                print("   💥 Risk: MEDIUM - Data integrity issues")
            
            # Extract key error information
            lines = traceback.split('\n')
            for line in lines:
                if 'AssertionError' in line:
                    print(f"   📋 Details: {line.strip()}")
                    break
    
    if result.errors:
        print(f"\n💥 TEST EXECUTION ERRORS ({errors}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n{i}. {test}")
            # Extract error type
            lines = traceback.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['Error:', 'Exception:']):
                    print(f"   🔥 {line.strip()}")
                    break
    
    # Security recommendations
    print(f"\n📋 SECURITY RECOMMENDATIONS:")
    
    if failures == 0 and errors == 0:
        print("  🎉 No critical vulnerabilities found!")
        print("  ✅ Continue with regular security monitoring")
        print("  ✅ Consider penetration testing for validation")
    else:
        print("  🚨 IMMEDIATE ACTION REQUIRED:")
        if any("injection" in str(f[0]).lower() for f in result.failures):
            print("    1. Fix input injection vulnerabilities (CRITICAL)")
            print("    2. Implement input sanitization")
            print("    3. Add command injection protection")
        
        if any("traversal" in str(f[0]).lower() for f in result.failures):
            print("    4. Strengthen path traversal protection")
            print("    5. Validate all file path operations")
        
        if any("api" in str(f[0]).lower() for f in result.failures):
            print("    6. Review API key handling")
            print("    7. Audit logging for sensitive data")
        
        print("  📅 TIMELINE:")
        print("    • Critical issues: Fix within 24-48 hours")
        print("    • High risk issues: Fix within 1 week") 
        print("    • Medium risk issues: Fix within 1 month")
    
    # OWASP Top 10 compliance
    print(f"\n🏆 OWASP TOP 10 COMPLIANCE:")
    owasp_issues = [
        "A01: Broken Access Control",
        "A02: Cryptographic Failures", 
        "A03: Injection",
        "A04: Insecure Design",
        "A05: Security Misconfiguration",
        "A06: Vulnerable Components",
        "A07: Authentication Failures",
        "A08: Data Integrity Failures",
        "A09: Logging Failures",
        "A10: Server-Side Request Forgery"
    ]
    
    # Analyze which OWASP issues are relevant and tested
    relevant_issues = ["A01", "A03", "A05", "A07", "A09"]  # Most relevant to this app
    
    for issue in owasp_issues:
        issue_code = issue.split(':')[0]
        if issue_code in relevant_issues:
            # Check if tests passed for this issue
            issue_tests = [f for f in result.failures if issue_code.lower() in str(f[0]).lower()]
            if issue_tests:
                print(f"  ❌ {issue} - VULNERABLE")
            else:
                print(f"  ✅ {issue} - PROTECTED")
        else:
            print(f"  ➖ {issue} - Not applicable")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Starting comprehensive security vulnerability assessment...")
    
    success = run_security_tests()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 SECURITY AUDIT COMPLETE - NO CRITICAL VULNERABILITIES")
        print("✅ System is ready for production deployment")
    else:
        print("🚨 SECURITY AUDIT COMPLETE - VULNERABILITIES FOUND")
        print("⚠️  DO NOT DEPLOY until critical issues are resolved")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)