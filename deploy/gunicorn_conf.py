import multiprocessing
import os

# # 设置工作目录并获取项目根目录的绝对路径
chdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

workers = 1

# 监听队列
backlog = 512

# 在单进程模式下，使用多线程来提高并发性
threads = int(os.environ.get('GUNICORN_THREADS', multiprocessing.cpu_count() * 2 + 1))

# 使用 Uvicorn 的 worker 类来运行 ASGI 应用
worker_class = "uvicorn.workers.UvicornWorker"

# 绑定的 IP 和端口
bind = os.environ.get("BIND", "0.0.0.0:8099")

# 日志目录
log_dir = os.environ.get('LOG_DIR', os.path.join(chdir, 'logs'))
# 确保日志目录存在
os.makedirs(log_dir, exist_ok=True)
loglevel = "INFO"  # 使用 DEBUG 级别以获取更详细的日志
accesslog = os.path.join(log_dir, 'gunicorn_access.log')
errorlog = os.path.join(log_dir, 'gunicorn_error.log')

# 在处理指定数量的请求后重启 workers
# 在单进程模式下，这可能不太必要，但仍可以保留以防内存泄漏
max_requests = 1000
max_requests_jitter = 50

# 请求超时时间（秒）
# 增加超时时间以适应长时间运行的 CUDA 操作
timeout = 3600

# 优雅的退出时间（秒）
graceful_timeout = 60

# 预加载应用
# 在单进程模式下，预加载可以确保 CUDA 初始化只发生一次
preload_app = False

# 守护进程模式
# 设置为 False 以便更容易调试
daemon = False

# 设置进程名称
proc_name = 'aitools_gunicorn'

# 设置 Gunicorn PID 文件路径
# pidfile = os.path.join(chdir, 'gunicorn.pid')

# 代码发生变化是否自动重启
# reload = True
