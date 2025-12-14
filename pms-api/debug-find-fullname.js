/**
 * 探索 ORDER_MN 所有欄位 - 尋找「洪榮宏」
 * 
 * 請將此檔案放到 PMS 伺服器 (192.168.8.3) 的 pms-api 目錄下執行：
 * node debug-find-fullname.js
 */

require('dotenv').config();
const oracledb = require('oracledb');

const BOOKING_ID = '00708801';
const SEARCH_NAME = '洪榮宏';

async function debugFindFullname() {
    console.log(`🔍 探索訂單 ${BOOKING_ID} 的所有欄位...\n`);

    let conn;
    try {
        const db = require('./config/database');
        await db.initialize();
        const pool = db.getPool();
        conn = await pool.getConnection();

        console.log('✅ 資料庫連線成功\n');

        // 1. 查詢 ORDER_MN 所有欄位
        console.log('========== ORDER_MN 所有欄位 ==========\n');
        const orderResult = await conn.execute(
            `SELECT * FROM GDWUUKT.ORDER_MN WHERE TRIM(IKEY) = :id`,
            [BOOKING_ID]
        );

        if (orderResult.rows.length > 0) {
            const row = orderResult.rows[0];
            orderResult.metaData.forEach((meta, idx) => {
                const value = row[idx];
                const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐ 找到了！' : '';
                // 特別標記可能與姓名相關的欄位
                const nameHint = meta.name.includes('NAM') || meta.name.includes('NAME') ||
                    meta.name.includes('GUEST') || meta.name.includes('LOCAL') ||
                    meta.name.includes('FULL') ? ' 📛' : '';
                console.log(`${meta.name}${nameHint}: ${valueStr}${highlight}`);
            });
        }

        // 2. 查詢 GUEST_MT（如果存在）
        console.log('\n\n========== GUEST_MT 住客資料表 ==========\n');
        try {
            const guestResult = await conn.execute(
                `SELECT * FROM GDWUUKT.GUEST_MT WHERE TRIM(ORDER_NO) = :id`,
                [BOOKING_ID]
            );

            if (guestResult.rows.length > 0) {
                guestResult.rows.forEach((row, rowIdx) => {
                    console.log(`\n--- 住客 ${rowIdx + 1} ---`);
                    guestResult.metaData.forEach((meta, idx) => {
                        const value = row[idx];
                        const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                        const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐ 找到了！' : '';
                        const nameHint = meta.name.includes('NAM') || meta.name.includes('NAME') ||
                            meta.name.includes('GUEST') || meta.name.includes('LOCAL') ||
                            meta.name.includes('FULL') ? ' 📛' : '';
                        console.log(`${meta.name}${nameHint}: ${valueStr}${highlight}`);
                    });
                });
            } else {
                console.log('無 GUEST_MT 資料');
            }
        } catch (err) {
            console.log('GUEST_MT 查詢失敗:', err.message.split('\n')[0]);
        }

        // 3. 查詢 ASSIGN_DT（分配房間資料）
        console.log('\n\n========== ASSIGN_DT 房間分配資料 ==========\n');
        try {
            const assignResult = await conn.execute(
                `SELECT * FROM GDWUUKT.ASSIGN_DT WHERE TRIM(IKEY) = :id`,
                [BOOKING_ID]
            );

            if (assignResult.rows.length > 0) {
                assignResult.rows.forEach((row, rowIdx) => {
                    console.log(`\n--- 分配 ${rowIdx + 1} ---`);
                    assignResult.metaData.forEach((meta, idx) => {
                        const value = row[idx];
                        const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                        const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐ 找到了！' : '';
                        const nameHint = meta.name.includes('NAM') || meta.name.includes('NAME') ||
                            meta.name.includes('GUEST') || meta.name.includes('LOCAL') ||
                            meta.name.includes('FULL') ? ' 📛' : '';
                        console.log(`${meta.name}${nameHint}: ${valueStr}${highlight}`);
                    });
                });
            } else {
                console.log('無 ASSIGN_DT 資料');
            }
        } catch (err) {
            console.log('ASSIGN_DT 查詢失敗:', err.message.split('\n')[0]);
        }

        await conn.close();
        await db.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }

    console.log('\n\n✅ 探索完成！');
    console.log(`請尋找包含 "${SEARCH_NAME}" 的欄位，那就是「住房登記姓名」欄位。`);
}

debugFindFullname().catch(console.error);
