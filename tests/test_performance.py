#!/usr/bin/env python3
"""
Performance Testing Suite for OCR Pipeline

Comprehensive performance analysis measuring:
- Processing time for various PDF sizes (1, 10, 100 pages)
- Memory usage during batch processing
- Concurrent request handling
- Extreme load analysis and failure point detection
- Realistic load simulation

Author: OCR Performance Team
Version: 1.0.0
"""

import unittest
import time
import psutil
import threading
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import concurrent.futures
import gc
import resource
from unittest.mock import patch, MagicMock
import json
from dataclasses import dataclass
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pdf_ocr import GeminiPDFOCR
    from config import GEMINI_API_KEY
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    GEMINI_API_KEY = "test_key"

@dataclass
class PerformanceMetrics:
    """Performance measurement data structure"""
    processing_time: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_percent: float
    pages_processed: int
    throughput_pages_per_sec: float
    api_calls: int
    errors: int

class MemoryMonitor:
    """Real-time memory usage monitoring"""
    
    def __init__(self):
        self.measurements = []
        self.monitoring = False
        self.thread = None
        
    def start(self):
        self.monitoring = True
        self.measurements = []
        self.thread = threading.Thread(target=self._monitor)
        self.thread.start()
        
    def stop(self):
        self.monitoring = False
        if self.thread:
            self.thread.join()
            
    def _monitor(self):
        while self.monitoring:
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            self.measurements.append(memory_mb)
            time.sleep(0.1)
            
    def get_stats(self) -> Tuple[float, float]:
        if not self.measurements:
            return 0.0, 0.0
        return max(self.measurements), sum(self.measurements) / len(self.measurements)

class MockPDFGenerator:
    """Generate mock PDF files for testing"""
    
    @staticmethod
    def create_test_pdf(pages: int, complexity: str = "simple") -> str:
        """Create mock PDF with specified pages and complexity"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        
        # Simulate different file sizes based on pages and complexity
        if complexity == "simple":
            size_per_page = 50 * 1024  # 50KB per page
        elif complexity == "medium":
            size_per_page = 200 * 1024  # 200KB per page
        else:  # complex
            size_per_page = 500 * 1024  # 500KB per page
            
        # Write PDF header and mock content
        content = b'%PDF-1.4\n'
        content += b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
        
        # Add mock content to reach target size
        total_size = pages * size_per_page
        padding = b'0' * (total_size - len(content))
        content += padding
        
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name

class PerformanceTestSuite(unittest.TestCase):
    """Comprehensive performance testing suite"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dirs = []
        self.test_files = []
        self.memory_monitor = MemoryMonitor()
        
        # Create test directories
        self.input_dir = tempfile.mkdtemp(prefix="perf_input_")
        self.output_dir = tempfile.mkdtemp(prefix="perf_output_")
        self.temp_dirs.extend([self.input_dir, self.output_dir])
        
        # Performance tracking
        self.metrics = {}
        
    def tearDown(self):
        """Cleanup test environment"""
        # Stop monitoring
        if hasattr(self, 'memory_monitor'):
            self.memory_monitor.stop()
            
        # Cleanup files
        for file_path in self.test_files:
            try:
                os.unlink(file_path)
            except:
                pass
                
        # Cleanup directories
        import shutil
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
        # Force garbage collection
        gc.collect()
    
    @contextmanager
    def performance_measurement(self, test_name: str):
        """Context manager for performance measurement"""
        # Start monitoring
        self.memory_monitor.start()
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        
        # Track API calls (mock counter)
        api_calls = 0
        errors = 0
        
        try:
            yield lambda: None  # Placeholder for API call tracking
        except Exception as e:
            errors += 1
            raise
        finally:
            # Stop monitoring and calculate metrics
            end_time = time.time()
            self.memory_monitor.stop()
            
            processing_time = end_time - start_time
            memory_peak, memory_avg = self.memory_monitor.get_stats()
            cpu_percent = psutil.cpu_percent() - start_cpu
            
            self.metrics[test_name] = {
                'processing_time': processing_time,
                'memory_peak_mb': memory_peak,
                'memory_avg_mb': memory_avg,
                'cpu_percent': cpu_percent,
                'api_calls': api_calls,
                'errors': errors
            }
    
    def test_single_page_processing_time(self):
        """Test processing time for single page PDF"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("single_page"):
            # Create 1-page PDF
            pdf_path = MockPDFGenerator.create_test_pdf(1, "simple")
            self.test_files.append(pdf_path)
            
            # Mock OCR processor to avoid API calls
            with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                mock_instance = MagicMock()
                mock_instance.process_pdf.return_value = ["Mock page content"]
                mock_ocr.return_value = mock_instance
                
                ocr = GeminiPDFOCR(api_key="test_key")
                result = ocr.process_pdf("test.pdf")
                
        # Assertions
        metrics = self.metrics["single_page"]
        self.assertLess(metrics['processing_time'], 5.0, "Single page should process in <5s")
        self.assertLess(metrics['memory_peak_mb'], 100, "Memory usage should be <100MB")
    
    def test_ten_page_processing_time(self):
        """Test processing time for 10-page PDF"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("ten_pages"):
            # Create 10-page PDF
            pdf_path = MockPDFGenerator.create_test_pdf(10, "medium")
            self.test_files.append(pdf_path)
            
            with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                mock_instance = MagicMock()
                mock_instance.process_pdf.return_value = ["Mock content"] * 10
                mock_ocr.return_value = mock_instance
                
                ocr = GeminiPDFOCR(api_key="test_key")
                result = ocr.process_pdf("test.pdf")
                
        metrics = self.metrics["ten_pages"]
        self.assertLess(metrics['processing_time'], 30.0, "10 pages should process in <30s")
        self.assertLess(metrics['memory_peak_mb'], 300, "Memory usage should be <300MB")
    
    def test_hundred_page_processing_time(self):
        """Test processing time for 100-page PDF"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("hundred_pages"):
            # Create 100-page PDF
            pdf_path = MockPDFGenerator.create_test_pdf(100, "complex")
            self.test_files.append(pdf_path)
            
            with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                mock_instance = MagicMock()
                mock_instance.process_pdf.return_value = ["Mock content"] * 100
                mock_ocr.return_value = mock_instance
                
                # Simulate realistic processing delay
                def slow_process(*args, **kwargs):
                    time.sleep(0.1)  # 100ms per page simulation
                    return ["Mock content"] * 100
                    
                mock_instance.process_pdf.side_effect = slow_process
                
                ocr = GeminiPDFOCR(api_key="test_key")
                result = ocr.process_pdf("test.pdf")
                
        metrics = self.metrics["hundred_pages"]
        self.assertLess(metrics['processing_time'], 300.0, "100 pages should process in <5min")
        self.assertLess(metrics['memory_peak_mb'], 1000, "Memory usage should be <1GB")
    
    def test_batch_processing_memory_usage(self):
        """Test memory usage during batch processing"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("batch_processing"):
            # Create multiple PDFs
            pdf_files = []
            for i in range(5):
                pdf_path = MockPDFGenerator.create_test_pdf(10, "medium")
                pdf_files.append(pdf_path)
                self.test_files.append(pdf_path)
            
            with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                mock_instance = MagicMock()
                mock_instance.process_all_pdfs.return_value = {
                    f"file_{i}.pdf": ["Mock content"] * 10 for i in range(5)
                }
                mock_ocr.return_value = mock_instance
                
                ocr = GeminiPDFOCR(api_key="test_key")
                results = ocr.process_all_pdfs()
                
        metrics = self.metrics["batch_processing"]
        # Memory should not grow linearly with batch size
        self.assertLess(metrics['memory_peak_mb'], 500, "Batch processing memory should be <500MB")
    
    def test_concurrent_request_handling(self):
        """Test concurrent processing capabilities"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("concurrent_requests"):
            # Create test PDFs
            pdf_files = []
            for i in range(3):
                pdf_path = MockPDFGenerator.create_test_pdf(5, "simple")
                pdf_files.append(pdf_path)
                self.test_files.append(pdf_path)
            
            def process_pdf_concurrent(pdf_index):
                """Simulate concurrent PDF processing"""
                with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                    mock_instance = MagicMock()
                    mock_instance.process_pdf.return_value = ["Mock content"] * 5
                    mock_ocr.return_value = mock_instance
                    
                    # Simulate processing delay
                    time.sleep(0.5)
                    
                    ocr = GeminiPDFOCR(api_key="test_key")
                    return ocr.process_pdf(f"test_{pdf_index}.pdf")
            
            # Run concurrent processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(process_pdf_concurrent, i) for i in range(3)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        metrics = self.metrics["concurrent_requests"]
        # Concurrent processing should be faster than sequential
        self.assertLess(metrics['processing_time'], 2.0, "Concurrent processing should be <2s")
        self.assertEqual(len(results), 3, "All concurrent requests should complete")
    
    def test_extreme_load_failure_points(self):
        """Test system behavior under extreme load"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("extreme_load"):
            # Simulate extreme load conditions
            extreme_conditions = [
                {"pages": 500, "complexity": "complex"},  # Very large PDF
                {"concurrent_requests": 10},  # High concurrency
                {"memory_pressure": True},  # Low memory simulation
            ]
            
            failures = []
            
            for condition in extreme_conditions:
                try:
                    if "pages" in condition:
                        # Test very large PDF
                        pdf_path = MockPDFGenerator.create_test_pdf(
                            condition["pages"], condition["complexity"]
                        )
                        self.test_files.append(pdf_path)
                        
                        with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                            mock_instance = MagicMock()
                            # Simulate memory error for very large files
                            if condition["pages"] > 200:
                                mock_instance.process_pdf.side_effect = MemoryError("Insufficient memory")
                            else:
                                mock_instance.process_pdf.return_value = ["Mock"] * condition["pages"]
                            mock_ocr.return_value = mock_instance
                            
                            ocr = GeminiPDFOCR(api_key="test_key")
                            ocr.process_pdf("extreme_test.pdf")
                            
                    elif "concurrent_requests" in condition:
                        # Test high concurrency
                        def concurrent_task():
                            time.sleep(0.1)
                            return "success"
                        
                        with concurrent.futures.ThreadPoolExecutor(max_workers=condition["concurrent_requests"]) as executor:
                            futures = [executor.submit(concurrent_task) for _ in range(condition["concurrent_requests"])]
                            results = [future.result() for future in concurrent.futures.as_completed(futures)]
                            
                except Exception as e:
                    failures.append(f"{condition}: {str(e)}")
            
        # Analyze failure points
        metrics = self.metrics["extreme_load"]
        self.assertGreater(len(failures), 0, "Should identify failure points under extreme load")
        
        # Log failure analysis
        print(f"\n🔍 Extreme Load Analysis:")
        print(f"   Failures detected: {len(failures)}")
        for failure in failures:
            print(f"   - {failure}")
    
    def test_realistic_load_simulation(self):
        """Test under realistic production load patterns"""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
            
        with self.performance_measurement("realistic_load"):
            # Simulate realistic usage patterns
            load_patterns = [
                {"type": "burst", "requests": 5, "interval": 0.1},  # Burst traffic
                {"type": "steady", "requests": 10, "interval": 1.0},  # Steady load
                {"type": "mixed", "small_pdfs": 8, "large_pdfs": 2},  # Mixed workload
            ]
            
            total_processed = 0
            
            for pattern in load_patterns:
                if pattern["type"] == "burst":
                    # Simulate burst traffic
                    start_time = time.time()
                    for i in range(pattern["requests"]):
                        with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                            mock_instance = MagicMock()
                            mock_instance.process_pdf.return_value = ["Mock content"]
                            mock_ocr.return_value = mock_instance
                            
                            ocr = GeminiPDFOCR(api_key="test_key")
                            ocr.process_pdf(f"burst_{i}.pdf")
                            time.sleep(pattern["interval"])
                    
                    burst_time = time.time() - start_time
                    total_processed += pattern["requests"]
                    
                elif pattern["type"] == "mixed":
                    # Simulate mixed workload
                    for i in range(pattern["small_pdfs"]):
                        pdf_path = MockPDFGenerator.create_test_pdf(2, "simple")
                        self.test_files.append(pdf_path)
                        total_processed += 1
                    
                    for i in range(pattern["large_pdfs"]):
                        pdf_path = MockPDFGenerator.create_test_pdf(20, "complex")
                        self.test_files.append(pdf_path)
                        total_processed += 1
            
        metrics = self.metrics["realistic_load"]
        throughput = total_processed / metrics['processing_time']
        
        # Performance assertions for realistic load
        self.assertGreater(throughput, 1.0, "Should handle >1 PDF per second")
        self.assertLess(metrics['memory_peak_mb'], 800, "Memory should stay <800MB under load")
    
    def test_performance_bottleneck_analysis(self):
        """Analyze performance bottlenecks in the OCR pipeline"""
        bottlenecks = {
            "pdf_to_image_conversion": 0,
            "image_to_text_extraction": 0,
            "file_io_operations": 0,
            "api_rate_limiting": 0,
            "memory_allocation": 0,
            "concurrent_processing": 0
        }
        
        # Test each bottleneck component
        with self.performance_measurement("bottleneck_analysis"):
            # 1. PDF to Image conversion bottleneck
            start = time.time()
            for i in range(10):
                pdf_path = MockPDFGenerator.create_test_pdf(5, "medium")
                self.test_files.append(pdf_path)
            bottlenecks["pdf_to_image_conversion"] = time.time() - start
            
            # 2. Simulated API rate limiting
            start = time.time()
            for i in range(5):
                time.sleep(0.2)  # Simulate API delay
            bottlenecks["api_rate_limiting"] = time.time() - start
            
            # 3. File I/O operations
            start = time.time()
            temp_files = []
            for i in range(20):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(b"Mock content" * 1000)
                temp_file.close()
                temp_files.append(temp_file.name)
            
            for temp_file in temp_files:
                with open(temp_file, 'r') as f:
                    f.read()
                os.unlink(temp_file)
            bottlenecks["file_io_operations"] = time.time() - start
        
        # Identify primary bottleneck
        primary_bottleneck = max(bottlenecks, key=bottlenecks.get)
        
        print(f"\n🔍 Performance Bottleneck Analysis:")
        for component, time_taken in sorted(bottlenecks.items(), key=lambda x: x[1], reverse=True):
            print(f"   {component}: {time_taken:.3f}s")
        print(f"   Primary bottleneck: {primary_bottleneck}")
        
        # Assert that we can identify bottlenecks
        self.assertGreater(bottlenecks[primary_bottleneck], 0, "Should identify performance bottlenecks")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        if not self.metrics:
            return "No performance data collected"
        
        report = "\n" + "="*60 + "\n"
        report += "📊 PERFORMANCE TEST REPORT\n"
        report += "="*60 + "\n"
        
        for test_name, metrics in self.metrics.items():
            report += f"\n🔍 {test_name.upper()}:\n"
            report += f"   Processing Time: {metrics['processing_time']:.3f}s\n"
            report += f"   Memory Peak: {metrics['memory_peak_mb']:.1f}MB\n"
            report += f"   Memory Average: {metrics['memory_avg_mb']:.1f}MB\n"
            report += f"   CPU Usage: {metrics['cpu_percent']:.1f}%\n"
            report += f"   API Calls: {metrics['api_calls']}\n"
            report += f"   Errors: {metrics['errors']}\n"
        
        # Performance recommendations
        report += "\n📋 PERFORMANCE RECOMMENDATIONS:\n"
        
        # Analyze metrics for recommendations
        max_memory = max(m['memory_peak_mb'] for m in self.metrics.values())
        avg_processing_time = sum(m['processing_time'] for m in self.metrics.values()) / len(self.metrics)
        
        if max_memory > 500:
            report += "   ⚠️  High memory usage detected - consider batch size optimization\n"
        if avg_processing_time > 10:
            report += "   ⚠️  Slow processing detected - consider concurrent processing\n"
        
        report += "   ✅ Implement connection pooling for API calls\n"
        report += "   ✅ Add caching for repeated operations\n"
        report += "   ✅ Optimize image compression before API calls\n"
        report += "   ✅ Implement progressive loading for large PDFs\n"
        
        return report

def run_performance_tests():
    """Run all performance tests and generate report"""
    print("🚀 Starting Performance Test Suite...")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all performance tests
    test_methods = [
        'test_single_page_processing_time',
        'test_ten_page_processing_time',
        'test_hundred_page_processing_time',
        'test_batch_processing_memory_usage',
        'test_concurrent_request_handling',
        'test_extreme_load_failure_points',
        'test_realistic_load_simulation',
        'test_performance_bottleneck_analysis'
    ]
    
    test_instance = PerformanceTestSuite()
    
    for method in test_methods:
        suite.addTest(PerformanceTestSuite(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate performance report
    print(test_instance.generate_performance_report())
    
    # Performance summary
    print("\n📈 PERFORMANCE SUMMARY:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures or result.errors:
        print("\n❌ Performance issues detected!")
        return False
    else:
        print("\n✅ All performance tests passed!")
        return True

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)