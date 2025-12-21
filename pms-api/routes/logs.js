/**
 * LOG 日誌相關路由
 * 
 * 提供遠端讀取伺服器 LOG 的 API
 */

const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, '..', 'logs');

/**
 * GET /api/logs
 * 取得可用的 LOG 檔案列表
 */
router.get('/', (req, res) => {
    try {
        if (!fs.existsSync(LOG_DIR)) {
            return res.json({
                success: true,
                data: {
                    files: [],
                    message: 'LOG 目錄尚未建立'
                }
            });
        }

        const files = fs.readdirSync(LOG_DIR)
            .filter(f => f.startsWith('pms_api_') && f.endsWith('.log'))
            .sort()
            .reverse()  // 最新的在前面
            .map(f => {
                const stats = fs.statSync(path.join(LOG_DIR, f));
                return {
                    filename: f,
                    date: f.replace('pms_api_', '').replace('.log', ''),
                    size: stats.size,
                    sizeFormatted: formatBytes(stats.size),
                    modified: stats.mtime.toISOString()
                };
            });

        res.json({
            success: true,
            data: {
                files,
                logDir: LOG_DIR,
                count: files.length
            }
        });
    } catch (err) {
        console.error('讀取 LOG 列表失敗：', err);
        res.status(500).json({
            success: false,
            error: {
                code: 'LOG_LIST_ERROR',
                message: err.message
            }
        });
    }
});

/**
 * GET /api/logs/today
 * 取得今日 LOG 內容
 */
router.get('/today', (req, res) => {
    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(LOG_DIR, `pms_api_${today}.log`);

    readLogFile(logFile, req, res);
});

/**
 * GET /api/logs/:date
 * 取得指定日期的 LOG 內容
 * @param date - 日期格式 YYYY-MM-DD
 */
router.get('/:date', (req, res) => {
    const { date } = req.params;

    // 驗證日期格式
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        return res.status(400).json({
            success: false,
            error: {
                code: 'INVALID_DATE_FORMAT',
                message: '日期格式必須為 YYYY-MM-DD'
            }
        });
    }

    const logFile = path.join(LOG_DIR, `pms_api_${date}.log`);
    readLogFile(logFile, req, res);
});

/**
 * 讀取 LOG 檔案內容
 */
function readLogFile(logFile, req, res) {
    try {
        if (!fs.existsSync(logFile)) {
            return res.status(404).json({
                success: false,
                error: {
                    code: 'LOG_NOT_FOUND',
                    message: `找不到 LOG 檔案: ${path.basename(logFile)}`
                }
            });
        }

        const content = fs.readFileSync(logFile, 'utf8');
        const lines = content.split('\n').filter(l => l.trim());

        // 查詢參數處理
        const { tail, level, search } = req.query;
        let filteredLines = lines;

        // 過濾 level (ERROR, ORACLE, REQUEST, RESPONSE, INFO, DEBUG)
        if (level) {
            const levels = level.toUpperCase().split(',');
            filteredLines = filteredLines.filter(line =>
                levels.some(l => line.includes(`| ${l} |`))
            );
        }

        // 搜尋關鍵字
        if (search) {
            filteredLines = filteredLines.filter(line =>
                line.toLowerCase().includes(search.toLowerCase())
            );
        }

        // 取最後 N 行
        if (tail) {
            const n = parseInt(tail, 10);
            if (!isNaN(n) && n > 0) {
                filteredLines = filteredLines.slice(-n);
            }
        }

        res.json({
            success: true,
            data: {
                filename: path.basename(logFile),
                totalLines: lines.length,
                filteredLines: filteredLines.length,
                content: filteredLines.join('\n'),
                lines: filteredLines
            }
        });
    } catch (err) {
        console.error('讀取 LOG 失敗：', err);
        res.status(500).json({
            success: false,
            error: {
                code: 'LOG_READ_ERROR',
                message: err.message
            }
        });
    }
}

/**
 * 格式化檔案大小
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

module.exports = router;
