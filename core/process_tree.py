import os
import time

class ProcessTreeReader:
    def __init__(self):
        # We store previous state for delta CPU calculation per process
        # Dict[pid, {'total_time': float, 'sys_uptime': float}]
        self._prev_states = {}
        
        # We reuse this list to avoid GC
        self._current_processes = []
        
        # System jiffies (Hz) - usually 100 on Linux, but we can compute it relative to system total
        self._hz = os.sysconf(os.sysconf_names['SC_CLK_TCK']) if 'SC_CLK_TCK' in os.sysconf_names else 100.0

    def get_system_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                return float(f.readline().split()[0])
        except Exception:
            return time.time()

    def update_processes(self):
        """Reads /proc and updates process list. Handles PermissionErrors."""
        self._current_processes.clear()
        sys_uptime = self.get_system_uptime()
        
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        current_pids_set = set()
        
        for pid_str in pids:
            pid = int(pid_str)
            current_pids_set.add(pid)
            
            try:
                # Read process stat
                with open(f'/proc/{pid}/stat', 'r') as f:
                    stat_content = f.read()
                
                # The command name is in parentheses, which might contain spaces.
                # Find the last parenthesis to safely split the rest.
                rparen_idx = stat_content.rfind(')')
                lparen_idx = stat_content.find('(')
                
                if rparen_idx == -1 or lparen_idx == -1:
                    continue
                    
                name = stat_content[lparen_idx+1:rparen_idx]
                parts = stat_content[rparen_idx+2:].split()
                
                # Status: R, S, D, Z, T, t, W, X, x, K, W, P
                state = parts[0]
                ppid = int(parts[1])
                
                # Indices in 'parts' array (shifted because name is extracted)
                # utime is 11, stime is 12 (in 0-indexed parts array after name)
                utime = float(parts[11])
                stime = float(parts[12])
                
                # RSS is 21
                rss_pages = float(parts[21])
                rss_mb = (rss_pages * 4096) / (1024 * 1024) # Assuming 4KB pages
                
                total_time = utime + stime
                
                # Calculate CPU %
                cpu_percent = 0.0
                if pid in self._prev_states:
                    prev = self._prev_states[pid]
                    delta_time = total_time - prev['total_time']
                    delta_sys = sys_uptime - prev['sys_uptime']
                    
                    if delta_sys > 0:
                        # (delta_time / HZ) / delta_uptime
                        cpu_percent = 100.0 * ((delta_time / self._hz) / delta_sys)
                
                # Update state for next cycle
                self._prev_states[pid] = {
                    'total_time': total_time,
                    'sys_uptime': sys_uptime
                }
                
                self._current_processes.append({
                    "pid": pid,
                    "ppid": ppid,
                    "name": name,
                    "cpu_percent": round(max(0.0, cpu_percent), 1),
                    "ram_mb": round(rss_mb, 1)
                })
                
            except PermissionError:
                # Silently ignore processes we don't have permission to read fully
                continue
            except FileNotFoundError:
                # Process might have terminated while reading
                continue
            except Exception:
                # Fallback for any parsing issue
                continue
                
        # Clean up old pids from state to prevent memory leak
        stale_pids = set(self._prev_states.keys()) - current_pids_set
        for p in stale_pids:
            del self._prev_states[p]
            
        # Sort by CPU usage descending
        self._current_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return self._current_processes

    @staticmethod
    def get_process_details(pid):
        details = {"cmdline": "غير متاح", "uid": "غير متاح", "user": "غير متاح"}
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmd = f.read().replace('\x00', ' ').strip()
                if cmd:
                    details["cmdline"] = cmd
        except Exception:
            pass
            
        try:
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if line.startswith("Uid:"):
                        uid = line.split()[1]
                        details["uid"] = uid
                        try:
                            import pwd
                            details["user"] = pwd.getpwuid(int(uid)).pw_name
                        except Exception:
                            pass
                        break
        except Exception:
            pass
            
        return details
