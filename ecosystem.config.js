module.exports = {
  apps: [{
    name: 'vehicular-system',
    script: 'main.py',
    interpreter: 'python3',
    watch: false,
    max_memory_restart: '200M',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    restart_delay: 1000,
    max_restarts: 10,
    min_uptime: '10s',
    env: {
      NODE_ENV: 'production',
      PORT: 8001
    },
    error_file: './logs/vehicular-error.log',
    out_file: './logs/vehicular-out.log',
    log_file: './logs/vehicular-combined.log',
    time: true
  }]
};
