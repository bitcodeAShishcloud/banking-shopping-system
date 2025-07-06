# Performance and Scalability Improvements

import asyncio
import threading
import time
from functools import wraps
import pickle
import os
from typing import Any, Dict, Optional
import logging

## 1. Caching System
class CacheManager:
    def __init__(self, cache_dir="./cache", max_size_mb=100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.access_times = {}
        
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        
        # Try to load from disk
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.cache[key] = data
                    self.access_times[key] = time.time()
                    return data
            except Exception:
                # Remove corrupted cache file
                os.remove(cache_file)
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set item in cache"""
        self.cache[key] = value
        self.access_times[key] = time.time()
        
        # Save to disk
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logging.warning(f"Failed to save cache to disk: {e}")
        
        # Clean up old entries if cache is too large
        self._cleanup_cache()
        
        # Set TTL if specified
        if ttl_seconds:
            threading.Timer(ttl_seconds, lambda: self.delete(key)).start()
    
    def delete(self, key: str):
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
        
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    
    def _cleanup_cache(self):
        """Remove least recently used items if cache is too large"""
        cache_size_mb = sum(
            os.path.getsize(os.path.join(self.cache_dir, f))
            for f in os.listdir(self.cache_dir)
            if f.endswith('.cache')
        ) / (1024 * 1024)
        
        if cache_size_mb > self.max_size_mb:
            # Sort by access time (least recent first)
            sorted_keys = sorted(self.access_times.keys(), 
                               key=lambda k: self.access_times[k])
            
            # Remove oldest 25% of entries
            items_to_remove = len(sorted_keys) // 4
            for key in sorted_keys[:items_to_remove]:
                self.delete(key)

# Global cache instance
cache_manager = CacheManager()

def cached(ttl_seconds=300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator

## 2. Asynchronous Operations
class AsyncTaskManager:
    def __init__(self):
        self.running_tasks = {}
        self.completed_tasks = {}
    
    async def run_task(self, task_id: str, coro):
        """Run an async task"""
        try:
            self.running_tasks[task_id] = asyncio.current_task()
            result = await coro
            self.completed_tasks[task_id] = {'status': 'success', 'result': result}
            return result
        except Exception as e:
            self.completed_tasks[task_id] = {'status': 'error', 'error': str(e)}
            raise
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task"""
        if task_id in self.running_tasks:
            return {'status': 'running'}
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        else:
            return {'status': 'not_found'}

## 3. Database Connection Pooling
import sqlite3
from queue import Queue
import threading

class ConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Initialize pool with connections
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            self.pool.put(conn)
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.get()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.put(conn)
    
    def execute_query(self, query: str, params=None):
        """Execute a query using pooled connection"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            return result
        finally:
            self.return_connection(conn)

## 4. Lazy Loading for Large Datasets
class LazyDataLoader:
    def __init__(self, data_source, page_size=50):
        self.data_source = data_source
        self.page_size = page_size
        self._cache = {}
        self._total_count = None
    
    def get_page(self, page_number: int):
        """Get a specific page of data"""
        if page_number in self._cache:
            return self._cache[page_number]
        
        offset = page_number * self.page_size
        
        if callable(self.data_source):
            # Data source is a function
            data = self.data_source(offset, self.page_size)
        else:
            # Data source is a list
            data = self.data_source[offset:offset + self.page_size]
        
        self._cache[page_number] = data
        return data
    
    def get_total_count(self):
        """Get total number of items"""
        if self._total_count is None:
            if callable(self.data_source):
                # For functions, we need a separate count method
                self._total_count = getattr(self.data_source, 'count', lambda: 0)()
            else:
                self._total_count = len(self.data_source)
        
        return self._total_count
    
    def get_total_pages(self):
        """Get total number of pages"""
        total_count = self.get_total_count()
        return (total_count + self.page_size - 1) // self.page_size

## 5. Background Task Processing
import queue
import threading

class BackgroundTaskProcessor:
    def __init__(self, num_workers=2):
        self.task_queue = queue.Queue()
        self.workers = []
        self.running = True
        
        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker, name=f"TaskWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Worker thread function"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                
                func, args, kwargs, callback = task
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        callback(result, None)
                except Exception as e:
                    if callback:
                        callback(None, e)
                
                self.task_queue.task_done()
            except queue.Empty:
                continue
    
    def submit_task(self, func, *args, callback=None, **kwargs):
        """Submit a task for background processing"""
        task = (func, args, kwargs, callback)
        self.task_queue.put(task)
    
    def shutdown(self):
        """Shutdown the task processor"""
        self.running = False
        
        # Add None tasks to wake up workers
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join()

## 6. Memory Usage Optimization
import gc
import psutil
import os

class MemoryManager:
    def __init__(self, warning_threshold_mb=500, critical_threshold_mb=800):
        self.warning_threshold = warning_threshold_mb * 1024 * 1024  # Convert to bytes
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
    
    def get_memory_usage(self):
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        return process.memory_info()
    
    def check_memory_usage(self):
        """Check if memory usage is within limits"""
        memory_info = self.get_memory_usage()
        current_usage = memory_info.rss
        
        if current_usage > self.critical_threshold:
            return 'critical'
        elif current_usage > self.warning_threshold:
            return 'warning'
        else:
            return 'normal'
    
    def cleanup_memory(self):
        """Force garbage collection and cleanup"""
        # Clear cache manager
        cache_manager.cache.clear()
        cache_manager.access_times.clear()
        
        # Force garbage collection
        gc.collect()
        
        print(f"Memory cleanup completed. Current usage: {self.get_memory_usage().rss / 1024 / 1024:.2f} MB")

## 7. Performance Monitoring
class PerformanceProfiler:
    def __init__(self):
        self.call_times = {}
        self.call_counts = {}
    
    def profile(self, func_name: str = None):
        """Decorator to profile function performance"""
        def decorator(func):
            name = func_name or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if name not in self.call_times:
                        self.call_times[name] = []
                        self.call_counts[name] = 0
                    
                    self.call_times[name].append(duration)
                    self.call_counts[name] += 1
            
            return wrapper
        return decorator
    
    def get_performance_report(self):
        """Get performance report"""
        report = {}
        
        for func_name in self.call_times:
            times = self.call_times[func_name]
            count = self.call_counts[func_name]
            
            report[func_name] = {
                'call_count': count,
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        return report

# Global instances
task_manager = AsyncTaskManager()
background_processor = BackgroundTaskProcessor()
memory_manager = MemoryManager()
profiler = PerformanceProfiler()

# Example usage decorators
@cached(ttl_seconds=600)  # Cache for 10 minutes
@profiler.profile()
def expensive_calculation(data):
    """Example of cached and profiled function"""
    # Simulate expensive operation
    time.sleep(0.1)
    return sum(data) if data else 0

# Cleanup function to call on app shutdown
def cleanup_performance_systems():
    """Cleanup all performance-related systems"""
    background_processor.shutdown()
    memory_manager.cleanup_memory()
    print("Performance systems cleaned up")

if __name__ == "__main__":
    # Example usage
    print("Testing performance improvements...")
    
    # Test caching
    result1 = expensive_calculation([1, 2, 3, 4, 5])
    result2 = expensive_calculation([1, 2, 3, 4, 5])  # Should be cached
    
    # Test background processing
    def background_task(x):
        time.sleep(0.5)
        return x * 2
    
    background_processor.submit_task(background_task, 5, callback=lambda r, e: print(f"Background result: {r}"))
    
    # Memory check
    memory_status = memory_manager.check_memory_usage()
    print(f"Memory status: {memory_status}")
    
    # Performance report
    time.sleep(1)  # Wait for background task
    report = profiler.get_performance_report()
    print("Performance Report:", report)
    
    # Cleanup
    cleanup_performance_systems()
