module.exports = {
  apps: [
    {
      name: "DT-Backend",
      script: "./src/index.js",
      cwd: "./ktw-backend",
      watch: true,
      env: {
        NODE_ENV: "production",
        PORT: 3000,
        PMS_API_URL: "http://192.168.8.3:3005/api",
        // PMS-API is running on remote server (192.168.8.3)
      },
    },
    /* PMS-API removed: Running on remote server
        {
            name: "PMS-API",
            script: "./server.js",
            cwd: "./pms-api",
            watch: true,
            env: {
                PORT: 3005
            }
        },
        */
    {
      name: "DT-Admin-Web",
      script: "npm",
      args: "run dev",
      cwd: "./ktw-admin-web",
      env: {
        PORT: 5002,
      },
    },
    {
      name: "Line-Bot-Py",
      script: "python3",
      args: "app.py",
      cwd: "./LINEBOT",
      watch: false,
      env: {
        PYTHONPATH: "..:../shared",
        PORT: 5001,
      },
    },
    {
      name: "Ngrok-Tunnel",
      script: "./ngrok",
      args: "http 5001",
      cwd: "./",
      watch: false,
    },
    {
      name: "Payload-CMS",
      script: "npm",
      args: "run dev",
      cwd: "../ktw-saas-platform",
      watch: false,
      env: {
        PORT: 3002,
      },
    },
    {
      name: "Transfer-SMS",
      script: "python3",
      args: "-u transfer_sms.py",
      cwd: "../ktw-oracle-to-pg/scripts/nec_pms",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
    {
      name: "oracle-log-monitor",
      script: "python3",
      args: "-u tail_windows_log.py -f",
      cwd: "../ktw-oracle-to-pg/scripts/export",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
    },
  ],
};
