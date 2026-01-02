bind = "0.0.0.0:$PORT"
workers = 1
worker_class = "sync"
worker_tmp_dir = "/dev/shm"
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
