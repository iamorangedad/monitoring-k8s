import time
import re
from prometheus_client import start_http_server, Gauge
from jtop import jtop

# --- 定义 Prometheus 指标 ---

# 1. 基础资源
# RAM 值是 0.17 (比率), 我们乘 100 转为百分比
RAM_USAGE = Gauge("jetson_ram_usage_percent", "Memory Usage %")
SWAP_USAGE = Gauge("jetson_swap_usage_percent", "Swap Usage %")
GPU_LOAD = Gauge("jetson_gpu_load_percent", "GPU Load %")

# 2. 温度 (根据您的数据，键名是 "Temp cpu" 和 "Temp gpu")
CPU_TEMP = Gauge("jetson_cpu_temp_celsius", "CPU Temperature (C)")
GPU_TEMP = Gauge("jetson_gpu_temp_celsius", "GPU Temperature (C)")
SOC_TEMP = Gauge(
    "jetson_soc_temp_celsius", "SOC Temperature (C)", ["sensor"]
)  # soc0, soc1, soc2

# 3. 功耗
POWER_TOT = Gauge("jetson_power_total_mw", "Total Power (mW)")
POWER_CPU_GPU = Gauge("jetson_power_cpu_gpu_mw", "Power VDD_CPU_GPU_CV (mW)")
POWER_SOC = Gauge("jetson_power_soc_mw", "Power VDD_SOC (mW)")

# 4. 风扇
FAN_SPEED = Gauge("jetson_fan_duty_cycle", "Fan Speed %")

# 5. CPU 多核负载 (使用标签区分核心)
CPU_CORE_LOAD = Gauge("jetson_cpu_core_load_percent", "CPU Core Load %", ["core_id"])


def collect_metrics():
    print("Connecting to jtop...")

    with jtop() as jetson:
        print(f"Jtop connected: {jetson.ok()}")

        while jetson.ok():
            # 获取当前快照
            stats = jetson.stats

            # --- 1. 读取基础负载 ---
            # .get(key, 0) 防止键不存在时报错
            GPU_LOAD.set(stats.get("GPU", 0.0))

            # RAM/SWAP 是 0.0-1.0 的比率，转为 0-100%
            RAM_USAGE.set(stats.get("RAM", 0.0) * 100)
            SWAP_USAGE.set(stats.get("SWAP", 0.0) * 100)

            # --- 2. 读取温度 (严格匹配您的键名) ---
            CPU_TEMP.set(stats.get("Temp cpu", 0.0))
            GPU_TEMP.set(stats.get("Temp gpu", 0.0))

            # 处理 SOC 温度 (Temp soc0, Temp soc1...)
            SOC_TEMP.labels(sensor="soc0").set(stats.get("Temp soc0", 0.0))
            SOC_TEMP.labels(sensor="soc1").set(stats.get("Temp soc1", 0.0))
            SOC_TEMP.labels(sensor="soc2").set(stats.get("Temp soc2", 0.0))

            # --- 3. 读取功耗 ---
            POWER_TOT.set(stats.get("Power TOT", 0.0))
            POWER_CPU_GPU.set(stats.get("Power VDD_CPU_GPU_CV", 0.0))
            POWER_SOC.set(stats.get("Power VDD_SOC", 0.0))

            # --- 4. 读取风扇 ---
            # 您的键名是 'Fan pwmfan0'
            FAN_SPEED.set(stats.get("Fan pwmfan0", 0.0))

            # --- 5. 读取 CPU 多核 ---
            # 遍历 stats 里的所有键，找到以 'CPU' 开头且后面是数字的键 (CPU1, CPU2...)
            for key, value in stats.items():
                if key.startswith("CPU") and key[3:].isdigit():
                    core_num = key[3:]  # 提取 '1', '2' 等
                    CPU_CORE_LOAD.labels(core_id=core_num).set(value)

            # 每 2 秒更新一次
            time.sleep(2)


if __name__ == "__main__":
    # 启动 HTTP 服务
    start_http_server(9800)
    print("Exporter running on port 9800...")
    collect_metrics()
