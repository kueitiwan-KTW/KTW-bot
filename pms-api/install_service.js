var Service = require('node-windows').Service;
var path = require('path');

// 1. 設定服務資訊
var svc = new Service({
    name: 'KTW Hotel PMS API',
    description: 'Host KTW Hotel PMS API for Line Bot (Port 3000)',
    script: path.join(__dirname, 'server.js'),
    nodeOptions: [
        '--harmony',
        '--max_old_space_size=4096'
    ]
    //, workingDirectory: '...'
    //, allowServiceLogon: true
});

// 2. 監聽安裝事件
svc.on('install', function () {
    console.log('✅ 服務安裝成功！');
    console.log('🚀 正在啟動服務...');
    svc.start();
});

svc.on('alreadyinstalled', function () {
    console.log('⚠️  服務已經安裝過了。');
    console.log('若要重新安裝，請先執行 uninstall_service.js');
});

svc.on('start', function () {
    console.log('✅ 服務已啟動！');
    console.log('您可以關閉此視窗，API 會在背景持續運作。');
    console.log('監控網址: http://localhost:3000/api/health');
});

svc.on('error', function (e) {
    console.log('❌ 發生錯誤:', e);
});

// 3. 執行安裝
console.log('📦 正在將 PMS API 安裝為 Windows服務...');
svc.install();
