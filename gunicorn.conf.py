# Gunicorn configuration for PDF Invoice Parser Web Service
# Production deployment settings

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/pdf-parser/access.log"
errorlog = "/var/log/pdf-parser/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pdf-parser-api"

# Daemon mode
daemon = False  # systemd will handle daemonization

# User and group (set appropriate user for your system)
user = "www-data"
group = "www-data"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True

# SSL (uncomment and configure if using HTTPS)
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"

# Startup/shutdown hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("PDF Invoice Parser starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("PDF Invoice Parser reloading...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("PDF Invoice Parser ready to serve requests")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("PDF Invoice Parser shutting down...")