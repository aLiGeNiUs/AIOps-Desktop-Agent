import time
import os

class SystemMetricsReader:
    def __init__(self):
        # Object pooling: Pre-allocate state variables to avoid instantiations
        self.last_cpu_total = 0.0
        self.last_cpu_idle = 0.0
        
        self.current_metrics = {
            "cpu_percent": 0.0,
            "ram_total_mb": 0.0,
            "ram_used_mb": 0.0,
            "ram_percent": 0.0,
            "timestamp": 0.0
        }
        
        # Initial read to populate last_* values
        self._read_cpu_raw()

    def _read_cpu_raw(self):
        """Reads raw cpu ticks from /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                first_line = f.readline()
                parts = first_line.split()
                if parts[0] == 'cpu':
                    # user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
                    values = [float(x) for x in parts[1:]]
                    idle = values[3] + values[4] # idle + iowait
                    total = sum(values)
                    return total, idle
        except Exception:
            pass
        return 0.0, 0.0

    def update_cpu_metrics(self):
        """Updates CPU metrics using delta calculation."""
        total, idle = self._read_cpu_raw()
        
        delta_total = total - self.last_cpu_total
        delta_idle = idle - self.last_cpu_idle
        
        if delta_total > 0:
            cpu_usage = 100.0 * (1.0 - (delta_idle / delta_total))
            self.current_metrics["cpu_percent"] = max(0.0, min(100.0, cpu_usage))
            
        self.last_cpu_total = total
        self.last_cpu_idle = idle

    def update_ram_metrics(self):
        """Reads /proc/meminfo and updates RAM metrics."""
        mem_total = 0.0
        mem_available = 0.0
        
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = float(line.split()[1]) # in kB
                    elif line.startswith("MemAvailable:"):
                        mem_available = float(line.split()[1]) # in kB
                    
                    if mem_total > 0 and mem_available > 0:
                        break # Found what we need
                        
        except Exception:
            pass

        if mem_total > 0:
            used = mem_total - mem_available
            self.current_metrics["ram_total_mb"] = mem_total / 1024.0
            self.current_metrics["ram_used_mb"] = used / 1024.0
            self.current_metrics["ram_percent"] = (used / mem_total) * 100.0

    def read_all(self):
        """Updates and returns all metrics in-place."""
        self.current_metrics["timestamp"] = time.time()
        self.update_cpu_metrics()
        self.update_ram_metrics()
        return self.current_metrics
