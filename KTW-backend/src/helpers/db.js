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

export default db;
