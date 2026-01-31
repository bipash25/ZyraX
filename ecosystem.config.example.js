module.exports = {
  apps: [{
    name: 'zyrax',
    script: 'bot.py',
    interpreter: 'python3.12',
    cwd: '/path/to/your/ZyraX',
    instances: 1,
    autorestart: true,
    watch: true,
    watch_delay: 1000,
    ignore_watch: [
      'node_modules',
      'data/logs',
      'data/sessions',
      'data/backups',
      '.git',
      '*.log',
      '__pycache__',
      '*.pyc',
      '.env',
      'ecosystem.config.js',
      '.pm2'
    ],
    max_memory_restart: '500M',
    error_file: './data/logs/pm2-error.log',
    out_file: './data/logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
}
