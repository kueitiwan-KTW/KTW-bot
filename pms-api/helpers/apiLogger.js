/**
 * PMS API Logger - 伺服器端日誌記錄器
 * 
 * 記錄所有 API 請求、Oracle 查詢、錯誤等
 * 自動清理 3 天前的 LOG
 */

const fs = require('fs');
const path = require('path');

// 設定
const LOG_DIR = path.join(__dirname, '..', 'logs');
const RETENTION_DAYS = 3;

// 確保 LOG 目錄存在
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

/**
 * 取得當前時間字串 (HH:MM:SS)
 */
function getTimeStr() {
    return new Date().toLocaleTimeString('zh-TW', { hour12: false });
}

/**
 * 取得當前日期字串 (YYYY-MM-DD)
 */
function getDateStr() {
    return new Date().toISOString().split('T')[0];
}

/**
 * 取得 LOG 檔案路徑
 */
function getLogPath() {
    return path.join(LOG_DIR, `pms_api_${getDateStr()}.log`);
}

/**
 * 寫入 LOG
 */
function writeLog(level, message) {
    const logLine = `${getTimeStr()} | ${level} | ${message}\n`;

    // 輸出到 console
    if (level === 'ERROR') {
        console.error(logLine.trim());
    } else {
        console.log(logLine.trim());
    }

    // 寫入檔案
    try {
        fs.appendFileSync(getLogPath(), logLine, 'utf8');
    } catch (err) {
        console.error(`無法寫入 LOG: ${err.message}`);
    }
}

/**
 * 清理舊 LOG 檔案 (超過 RETENTION_DAYS 天)
 */
function cleanupOldLogs() {
    try {
        const files = fs.readdirSync(LOG_DIR);
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - RETENTION_DAYS);

        files.forEach(file => {
            if (!file.startsWith('pms_api_') || !file.endsWith('.log')) return;

            // 從檔名提取日期 (pms_api_2025-12-21.log)
            const dateStr = file.replace('pms_api_', '').replace('.log', '');
            const fileDate = new Date(dateStr);

            if (fileDate < cutoffDate) {
                const filePath = path.join(LOG_DIR, file);
                fs.unlinkSync(filePath);
                console.log(`🗑️ 已清理舊 LOG: ${file}`);
            }
        });
    } catch (err) {
        console.error(`清理 LOG 時發生錯誤: ${err.message}`);
    }
}

// 啟動時清理舊 LOG
cleanupOldLogs();

// ===== 日誌方法 =====

/**
 * 記錄 API 請求
 */
function logRequest(method, url, params = {}) {
    const paramStr = Object.keys(params).length > 0
        ? ` | params=${JSON.stringify(params)}`
        : '';
    writeLog('REQUEST', `${method} ${url}${paramStr}`);
}

/**
 * 記錄 API 回應
 */
function logResponse(method, url, statusCode, elapsed, resultCount = null) {
    const countStr = resultCount !== null ? ` | count=${resultCount}` : '';
    writeLog('RESPONSE', `${method} ${url} | status=${statusCode} | elapsed=${elapsed}ms${countStr}`);
}

/**
 * 記錄 Oracle 查詢
 */
function logOracleQuery(operation, elapsed, rowCount = null) {
    const countStr = rowCount !== null ? ` | rows=${rowCount}` : '';
    writeLog('ORACLE', `${operation} | elapsed=${elapsed}ms${countStr}`);
}

/**
 * 記錄 Oracle 錯誤
 */
function logOracleError(operation, errorCode, errorMessage) {
    const msg = errorMessage.length > 150 ? errorMessage.substring(0, 150) + '...' : errorMessage;
    writeLog('ERROR', `ORACLE_${operation} | code=${errorCode} | message=${msg}`);
}

/**
 * 記錄一般錯誤
 */
function logError(type, message) {
    const msg = message.length > 200 ? message.substring(0, 200) + '...' : message;
    writeLog('ERROR', `${type} | ${msg}`);
}

/**
 * 記錄一般資訊
 */
function logInfo(message) {
    writeLog('INFO', message);
}

/**
 * 記錄除錯資訊
 */
function logDebug(message) {
    writeLog('DEBUG', message);
}

module.exports = {
    logRequest,
    logResponse,
    logOracleQuery,
    logOracleError,
    logError,
    logInfo,
    logDebug,
    cleanupOldLogs
};
