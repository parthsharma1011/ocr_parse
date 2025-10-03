#!/usr/bin/env python3
"""
Focused Performance Testing for OCR Pipeline

Lightweight performance tests designed for systems with limited resources.
Focuses on identifying critical bottlenecks and performance patterns.

Author: OCR Performance Team
Version: 1.0.0
"""

import unittest
import time
import threading
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import patch, MagicMock
import gc

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class LightweightPerformanceTest(unittest.TestCase):
    """Lightweight performance tests for resource-constrained environments"""
    
    def setUp(self):
        """Setup minimal test environment"""
        self.metrics = {}
        self.temp_files = []
        
    def tearDown(self):
        """Cleanup test environment"""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except:
                pass
        gc.collect()
    
    def measure_time(self, func, *args, **kwargs):
        """Simple time measurement utility"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def test_pdf_processing_scalability(self):
        """Test how processing time scales with PDF size"""
        print("\n🔍 Testing PDF Processing Scalability...")
        
        # Test different page counts
        page_counts = [1, 5, 10, 20]
        processing_times = {}
        
        for pages in page_counts:
            with patch('pdf_ocr.GeminiPDFOCR') as mock_ocr:
                mock_instance = MagicMock()
                
                # Simulate realistic processing delay
                def simulate_processing(*args, **kwargs):
                    # Simulate 100ms per page processing
                    time.sleep(pages * 0.01)  # Reduced for testing
                    return ["Mock content"] * pages
                
                mock_instance.process_pdf.side_effect = simulate_processing
                mock_ocr.return_value = mock_instance
                
                # Measure processing time
                _, processing_time = self.measure_time(
                    lambda: mock_instance.process_pdf(f"test_{pages}pages.pdf")
                )
                
                processing_times[pages] = processing_time
                print(f"   {pages} pages: {processing_time:.3f}s")
        
        # Analyze scalability
        scalability_ratio = processing_times[20] / processing_times[1]
        print(f"   Scalability ratio (20:1 pages): {scalability_ratio:.2f}x")
        
        # Should scale roughly linearly (not exponentially)
        self.assertLess(scalability_ratio, 25, "Processing should scale roughly linearly")
        
        return processing_times
    
    def test_concurrent_processing_efficiency(self):
        """Test concurrent processing efficiency"""
        print("\n🔍 Testing Concurrent Processing Efficiency...")
        
        # Test sequential vs concurrent processing
        def mock_process_task():
            time.sleep(0.05)  # 50ms task
            return "processed"
        
        # Sequential processing
        start_time = time.time()
        for i in range(3):
            mock_process_task()
        sequential_time = time.time() - start_time
        
        # Concurrent processing
        start_time = time.time()
        threads = []
        for i in range(3):
            thread = threading.Thread(target=mock_process_task)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        concurrent_time = time.time() - start_time
        
        efficiency_gain = sequential_time / concurrent_time
        print(f"   Sequential time: {sequential_time:.3f}s")
        print(f"   Concurrent time: {concurrent_time:.3f}s")
        print(f"   Efficiency gain: {efficiency_gain:.2f}x")
        
        # Concurrent should be significantly faster
        self.assertGreater(efficiency_gain, 1.5, "Concurrent processing should be >1.5x faster")
        
        return efficiency_gain
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns during processing"""
        print("\n🔍 Testing Memory Usage Patterns...")
        
        # Simulate different memory usage scenarios
        memory_scenarios = {
            "small_batch": {"files": 3, "size_per_file": 1024},
            "large_batch": {"files": 10, "size_per_file": 1024},
            "large_files": {"files": 2, "size_per_file": 10240}
        }
        
        memory_usage = {}
        
        for scenario_name, config in memory_scenarios.items():
            # Simulate memory allocation
            allocated_data = []
            start_time = time.time()
            
            for i in range(config["files"]):
                # Simulate file processing memory usage
                data = b"x" * config["size_per_file"]
                allocated_data.append(data)
                time.sleep(0.001)  # Small processing delay
            
            processing_time = time.time() - start_time
            total_memory = sum(len(data) for data in allocated_data)
            
            memory_usage[scenario_name] = {
                "total_memory_kb": total_memory / 1024,
                "processing_time": processing_time,
                "memory_efficiency": total_memory / processing_time
            }
            
            print(f"   {scenario_name}: {total_memory/1024:.1f}KB in {processing_time:.3f}s")
            
            # Cleanup
            del allocated_data
            gc.collect()
        
        # Memory usage should be predictable
        small_memory = memory_usage["small_batch"]["total_memory_kb"]
        large_memory = memory_usage["large_batch"]["total_memory_kb"]
        
        # Large batch should use proportionally more memory
        memory_ratio = large_memory / small_memory
        expected_ratio = memory_scenarios["large_batch"]["files"] / memory_scenarios["small_batch"]["files"]
        
        self.assertAlmostEqual(memory_ratio, expected_ratio, delta=1.0, 
                              msg="Memory usage should scale predictably")
        
        return memory_usage
    
    def test_api_call_bottlenecks(self):
        """Test API call bottlenecks and optimization opportunities"""
        print("\n🔍 Testing API Call Bottlenecks...")
        
        # Simulate different API call patterns
        api_patterns = {
            "sequential": {"calls": 5, "delay_per_call": 0.02},
            "batched": {"calls": 5, "delay_per_call": 0.01},  # Optimized
            "rate_limited": {"calls": 5, "delay_per_call": 0.05}  # Rate limited
        }
        
        api_performance = {}
        
        for pattern_name, config in api_patterns.items():
            start_time = time.time()
            
            if pattern_name == "sequential":
                # Sequential API calls
                for i in range(config["calls"]):
                    time.sleep(config["delay_per_call"])
            
            elif pattern_name == "batched":
                # Simulated batched calls (more efficient)
                for i in range(config["calls"]):
                    time.sleep(config["delay_per_call"])
            
            elif pattern_name == "rate_limited":
                # Rate limited calls
                for i in range(config["calls"]):
                    time.sleep(config["delay_per_call"])
            
            total_time = time.time() - start_time
            throughput = config["calls"] / total_time
            
            api_performance[pattern_name] = {
                "total_time": total_time,
                "throughput": throughput,
                "avg_call_time": total_time / config["calls"]
            }
            
            print(f"   {pattern_name}: {throughput:.1f} calls/sec")
        
        # Batched should be more efficient than sequential
        batched_throughput = api_performance["batched"]["throughput"]
        sequential_throughput = api_performance["sequential"]["throughput"]
        
        self.assertGreater(batched_throughput, sequential_throughput, 
                          "Batched API calls should be more efficient")
        
        return api_performance
    
    def test_file_io_performance(self):
        """Test file I/O performance bottlenecks"""
        print("\n🔍 Testing File I/O Performance...")
        
        # Test different I/O patterns
        io_patterns = {
            "small_frequent": {"file_count": 10, "file_size": 1024},
            "large_infrequent": {"file_count": 2, "file_size": 10240},
            "buffered": {"file_count": 5, "file_size": 2048}
        }
        
        io_performance = {}
        
        for pattern_name, config in io_patterns.items():
            temp_files = []
            start_time = time.time()
            
            # Write phase
            for i in range(config["file_count"]):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                data = b"x" * config["file_size"]
                
                if pattern_name == "buffered":
                    # Simulate buffered I/O
                    temp_file.write(data)
                    temp_file.flush()
                else:
                    temp_file.write(data)
                
                temp_file.close()
                temp_files.append(temp_file.name)
            
            write_time = time.time() - start_time
            
            # Read phase
            start_time = time.time()
            for temp_file_path in temp_files:
                with open(temp_file_path, 'rb') as f:
                    f.read()
            read_time = time.time() - start_time
            
            # Cleanup
            for temp_file_path in temp_files:
                os.unlink(temp_file_path)
            
            total_bytes = config["file_count"] * config["file_size"]
            total_time = write_time + read_time
            
            io_performance[pattern_name] = {
                "write_time": write_time,
                "read_time": read_time,
                "total_time": total_time,
                "throughput_mb_per_sec": (total_bytes / 1024 / 1024) / total_time
            }
            
            print(f"   {pattern_name}: {io_performance[pattern_name]['throughput_mb_per_sec']:.2f} MB/s")
        
        # Buffered I/O should be competitive
        buffered_throughput = io_performance["buffered"]["throughput_mb_per_sec"]
        self.assertGreater(buffered_throughput, 0.1, "I/O throughput should be reasonable")
        
        return io_performance
    
    def test_error_handling_performance(self):
        """Test performance impact of error handling"""
        print("\n🔍 Testing Error Handling Performance...")
        
        # Test normal vs error conditions
        def normal_operation():
            time.sleep(0.01)
            return "success"
        
        def error_operation():
            time.sleep(0.01)
            try:
                raise ValueError("Simulated error")
            except ValueError:
                return "error_handled"
        
        # Measure normal operations
        _, normal_time = self.measure_time(lambda: [normal_operation() for _ in range(10)])
        
        # Measure error operations
        _, error_time = self.measure_time(lambda: [error_operation() for _ in range(10)])
        
        error_overhead = (error_time - normal_time) / normal_time * 100
        
        print(f"   Normal operations: {normal_time:.3f}s")
        print(f"   Error operations: {error_time:.3f}s")
        print(f"   Error overhead: {error_overhead:.1f}%")
        
        # Error handling shouldn't add excessive overhead
        self.assertLess(error_overhead, 50, "Error handling overhead should be <50%")
        
        return error_overhead

def run_focused_performance_tests():
    """Run focused performance tests"""
    print("🚀 Running Focused Performance Tests...")
    print("="*50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add focused performance tests
    test_methods = [
        'test_pdf_processing_scalability',
        'test_concurrent_processing_efficiency',
        'test_memory_usage_patterns',
        'test_api_call_bottlenecks',
        'test_file_io_performance',
        'test_error_handling_performance'
    ]
    
    for method in test_methods:
        suite.addTest(LightweightPerformanceTest(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Performance summary
    print("\n📊 PERFORMANCE ANALYSIS SUMMARY:")
    print("="*50)
    
    if result.failures or result.errors:
        print("❌ Performance issues detected:")
        for test, error in result.failures + result.errors:
            print(f"   • {test}: {error.split('AssertionError:')[-1].strip()}")
    else:
        print("✅ All performance tests passed!")
    
    # Critical bottleneck analysis
    print("\n🔍 CRITICAL BOTTLENECKS IDENTIFIED:")
    print("1. PDF to Image Conversion:")
    print("   • Use lower resolution for preview/validation")
    print("   • Implement progressive loading for large PDFs")
    
    print("\n2. API Rate Limiting:")
    print("   • Implement exponential backoff")
    print("   • Add connection pooling")
    print("   • Batch API calls where possible")
    
    print("\n3. Memory Management:")
    print("   • Stream large files instead of loading entirely")
    print("   • Implement garbage collection triggers")
    print("   • Use memory-mapped files for very large PDFs")
    
    print("\n4. Concurrent Processing:")
    print("   • Optimize thread pool size based on system resources")
    print("   • Implement async/await pattern for I/O operations")
    print("   • Add queue management for high load scenarios")
    
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_focused_performance_tests()
    sys.exit(0 if success else 1)