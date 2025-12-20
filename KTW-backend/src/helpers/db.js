import sqlite3 from 'sqlite3';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync, mkdirSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 確保 data 目錄存在
const DATA_DIR = join(__dirname, '../../data');
if (!existsSync(DATA_DIR)) {
    mkdirSync(DATA_DIR, { recursive: true });
}

const DB_PATH = join(DATA_DIR, 'ktw_supplements.db');

const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('❌ 無法開啟 SQLite 資料庫:', err.message);
    } else {
        console.log('✅ 已連線到 SQLite 擴充資料庫');
        initDb();
    }
});

function initDb() {
    const schema = `
        CREATE TABLE IF NOT EXISTS guest_supplements (
            booking_id TEXT PRIMARY KEY,
            confirmed_phone TEXT,
            arrival_time TEXT,
            staff_memo TEXT,
            ai_extracted_requests TEXT,
            line_name TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `;
    db.run(schema, (err) => {
        if (err) {
            console.error('❌ 初始化資料庫失敗:', err.message);
        } else {
            console.log('✅ guest_supplements 資料表就緒');
            // 檢查是否需要新增 line_name 欄位 (遷移)
            db.all("PRAGMA table_info(guest_supplements)", (err, columns) => {
                if (!err && !columns.find(c => c.name === 'line_name')) {
                    db.run("ALTER TABLE guest_supplements ADD COLUMN line_name TEXT", (err) => {
                        if (!err) console.log('✅ 已升級資料庫：新增 line_name 欄位');
                        else console.error('❌ 升級資料庫失敗:', err.message);
                    });
                }
            });
        }
    });
}

/**
 * 取得訂單擴充資料
 */
export function getSupplement(bookingId) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM guest_supplements WHERE booking_id = ?', [bookingId], (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

/**
 * 批次取得訂單擴充資料
 */
export function getAllSupplements(bookingIds) {
    if (!bookingIds || bookingIds.length === 0) return Promise.resolve([]);
    const placeholders = bookingIds.map(() => '?').join(',');
    return new Promise((resolve, reject) => {
        db.all(`SELECT * FROM guest_supplements WHERE booking_id IN (${placeholders})`, bookingIds, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

/**
 * 更新或插入擴充資料
 */
export function updateSupplement(bookingId, data) {
    const { confirmed_phone, arrival_time, staff_memo, ai_extracted_requests, line_name } = data;
    const updatedAt = new Date().toISOString();

    return new Promise((resolve, reject) => {
        // 使用 REPLACE INTO (SQLite) 或 INSERT OR REPLACE
        const sql = `
            INSERT INTO guest_supplements (
                booking_id, confirmed_phone, arrival_time, staff_memo, ai_extracted_requests, line_name, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(booking_id) DO UPDATE SET
                confirmed_phone = COALESCE(excluded.confirmed_phone, confirmed_phone),
                arrival_time = COALESCE(excluded.arrival_time, arrival_time),
                staff_memo = COALESCE(excluded.staff_memo, staff_memo),
                ai_extracted_requests = COALESCE(excluded.ai_extracted_requests, ai_extracted_requests),
                line_name = COALESCE(excluded.line_name, line_name),
                updated_at = excluded.updated_at
        `;

        db.run(sql, [bookingId, confirmed_phone, arrival_time, staff_memo, ai_extracted_requests, line_name, updatedAt], function (err) {
            if (err) reject(err);
            else resolve({ changes: this.changes });
        });
    });
}

// ============================================
// Bot Session 持久化 (對話狀態儲存)
// ============================================

/**
 * 初始化 bot_sessions 資料表
 */
function initBotSessionsTable() {
    const schema = `
        CREATE TABLE IF NOT EXISTS bot_sessions (
            user_id TEXT PRIMARY KEY,
            handler_type TEXT,
            state TEXT,
            data TEXT,
            pending_intent TEXT,
            pending_intent_message TEXT,
            created_at DATETIME,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `;
    db.run(schema, (err) => {
        if (err) {
            console.error('❌ 初始化 bot_sessions 資料表失敗:', err.message);
        } else {
            console.log('✅ bot_sessions 資料表就緒');
        }
    });
}

// 在資料庫連線後初始化
setTimeout(initBotSessionsTable, 500);

/**
 * 取得 Bot Session
 * @param {string} userId - LINE 用戶 ID
 * @returns {Promise<Object|null>} session 資料
 */
export function getBotSession(userId) {
    return new Promise((resolve, reject) => {
        db.get('SELECT * FROM bot_sessions WHERE user_id = ?', [userId], (err, row) => {
            if (err) reject(err);
            else if (row) {
                // 解析 JSON 欄位
                try {
                    row.data = row.data ? JSON.parse(row.data) : {};
                } catch {
                    row.data = {};
                }
                resolve(row);
            } else {
                resolve(null);
            }
        });
    });
}

/**
 * 更新或建立 Bot Session
 * @param {string} userId - LINE 用戶 ID
 * @param {Object} sessionData - session 資料
 */
export function updateBotSession(userId, sessionData) {
    const { handler_type, state, data, pending_intent, pending_intent_message } = sessionData;
    const now = new Date().toISOString();
    const dataJson = JSON.stringify(data || {});

    return new Promise((resolve, reject) => {
        const sql = `
            INSERT INTO bot_sessions (
                user_id, handler_type, state, data, pending_intent, pending_intent_message, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                handler_type = excluded.handler_type,
                state = excluded.state,
                data = excluded.data,
                pending_intent = excluded.pending_intent,
                pending_intent_message = excluded.pending_intent_message,
                updated_at = excluded.updated_at
        `;

        db.run(sql, [userId, handler_type, state, dataJson, pending_intent, pending_intent_message, now, now], function (err) {
            if (err) reject(err);
            else resolve({ changes: this.changes });
        });
    });
}

/**
 * 刪除 Bot Session
 * @param {string} userId - LINE 用戶 ID
 */
export function deleteBotSession(userId) {
    return new Promise((resolve, reject) => {
        db.run('DELETE FROM bot_sessions WHERE user_id = ?', [userId], function (err) {
            if (err) reject(err);
            else resolve({ changes: this.changes });
        });
    });
}

export default db;

