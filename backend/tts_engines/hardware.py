import platform
import os
import psutil

def get_system_telemetry():
    """
    Detects operating system, CPU, memory, and acceleration hardware 
    (NVIDIA CUDA on Windows/Linux, Apple Silicon MPS on macOS Mac mini M4, etc.)
    """
    os_name = platform.system()
    os_release = platform.release()
    machine = platform.machine()
    processor = platform.processor() or "Unknown CPU"
    
    # CPU & RAM stats
    logical_cpus = psutil.cpu_count(logical=True) or 1
    physical_cpus = psutil.cpu_count(logical=False) or logical_cpus
    cpu_percent = psutil.cpu_percent(interval=None)
    
    vm = psutil.virtual_memory()
    total_ram_gb = round(vm.total / (1024 ** 3), 2)
    available_ram_gb = round(vm.available / (1024 ** 3), 2)
    ram_percent = vm.percent

    # Hardware acceleration detection
    accel_type = "CPU (Standard)"
    accel_device_name = f"{logical_cpus} Logical Cores"
    is_apple_silicon = False
    is_cuda_available = False
    is_mps_available = False

    # Check for Apple Silicon
    if os_name == "Darwin" and ("arm" in machine.lower() or "apple" in processor.lower() or machine == "arm64"):
        is_apple_silicon = True
        accel_type = "Apple Silicon Neural/Metal (M-Series)"
        accel_device_name = f"Apple M-Series ({machine})"

    # Check PyTorch devices if torch is installed
    try:
        import torch
        if torch.cuda.is_available():
            is_cuda_available = True
            accel_type = "NVIDIA CUDA Acceleration"
            accel_device_name = torch.cuda.get_device_name(0)
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            is_mps_available = True
            accel_type = "Apple Silicon MPS (Metal Performance Shaders)"
            accel_device_name = "Apple Silicon GPU / Neural Engine (MPS)"
    except Exception:
        pass

    # Windows fallback GPU check via environment or platform if torch not loaded yet
    if not is_cuda_available and os_name == "Windows":
        try:
            # Check for NVIDIA controller via wmic / CimInstance or environment
            pass
        except Exception:
            pass

    return {
        "os": os_name,
        "os_version": f"{os_name} {os_release} ({machine})",
        "processor": processor,
        "cpu_cores": f"{physical_cpus} physical / {logical_cpus} logical",
        "cpu_usage_percent": cpu_percent,
        "ram_total_gb": total_ram_gb,
        "ram_available_gb": available_ram_gb,
        "ram_usage_percent": ram_percent,
        "acceleration_type": accel_type,
        "device_name": accel_device_name,
        "is_apple_silicon": is_apple_silicon,
        "is_mps_available": is_mps_available,
        "is_cuda_available": is_cuda_available
    }

if __name__ == "__main__":
    import json
    print(json.dumps(get_system_telemetry(), indent=2))
