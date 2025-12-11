var Service = require('node-windows').Service;
var path = require('path');

// 設定服務資訊 (必須與安裝時相同)
var svc = new Service({
    name: 'KTW Hotel PMS API',
    script: path.join(__dirname, 'server.js')
});

// 監聽卸載事件
svc.on('uninstall', function () {
    console.log('✅ 服務已卸載完成。');
    console.log('服務名稱: KTW Hotel PMS API');
});

// 執行卸載
console.log('🗑️  正在卸載 Windows 服務...');
svc.uninstall();
