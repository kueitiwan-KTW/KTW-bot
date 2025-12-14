/**
 * PMS 資料表欄位探索工具
 * 目的：尋找「住房登記姓名」欄位
 * 
 * 執行方式：在 pms-api-poc 目錄下執行 node find-guest-name-columns.js
 */

require('dotenv').config();
const oracledb = require('oracledb');

// 可能包含住客登記資訊的資料表（依優先順序）
const TABLES_TO_CHECK = [
    'GDWUUKT.GUEST_MT',      // 住客主檔
    'GDWUUKT.GUEST_DT',      // 住客明細
    'GDWUUKT.REGISTR_MT',    // 登記主檔 (可能)
    'GDWUUKT.REGISTR_DT',    // 登記明細 (可能)
    'GDWUUKT.CHECKIN_MT',    // 入住主檔 (可能)
    'GDWUUKT.CHECKIN_DT',    // 入住明細 (可能)
    'GDWUUKT.ORDER_MT',      // 訂單主檔
    'GDWUUKT.ORDER_DT',      // 訂單明細
    'GDWUUKT.CUST_MT',       // 顧客主檔
];

// 姓名相關的關鍵字
const NAME_KEYWORDS = ['NAME', 'NAM', 'GUEST', 'REGIST', 'ID', 'PASSPORT', 'NATION'];

async function findGuestNameColumns() {
    console.log('🔍 開始搜尋住客登記姓名欄位...\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            connectString: process.env.DB_CONNECT_STRING,
            externalAuth: true
        });
        console.log('✅ 資料庫連線成功\n');

        for (const table of TABLES_TO_CHECK) {
            try {
                // 嘗試查詢資料表結構
                const result = await conn.execute(`SELECT * FROM ${table} WHERE ROWNUM=1`);
                const columns = result.metaData.map(m => m.name);

                // 過濾出可能與姓名相關的欄位
                const nameColumns = columns.filter(col =>
                    NAME_KEYWORDS.some(kw => col.toUpperCase().includes(kw))
                );

                console.log(`\n📋 ${table}`);
                console.log(`   全部欄位 (${columns.length}): ${columns.join(', ')}`);

                if (nameColumns.length > 0) {
                    console.log(`   ⭐ 姓名相關: ${nameColumns.join(', ')}`);
                }

                // 嘗試取得一筆樣本資料
                if (result.rows && result.rows.length > 0) {
                    const sampleRow = {};
                    columns.forEach((col, idx) => {
                        if (NAME_KEYWORDS.some(kw => col.toUpperCase().includes(kw))) {
                            sampleRow[col] = result.rows[0][idx];
                        }
                    });
                    if (Object.keys(sampleRow).length > 0) {
                        console.log(`   📊 樣本資料: ${JSON.stringify(sampleRow)}`);
                    }
                }

            } catch (err) {
                console.log(`\n❌ ${table}: ${err.message.split('\n')[0]}`);
            }
        }

        // 查詢今日已入住的訂單詳細資訊
        console.log('\n\n========================================');
        console.log('🏨 今日已入住訂單的姓名欄位查詢');
        console.log('========================================\n');

        try {
            const todayQuery = `
                SELECT 
                    om.ORDER_NO,
                    om.CUST_NAM,
                    om.RSV_DATE,
                    gm.GLAST_NAM,
                    gm.GFIRST_NAM,
                    gm.GENG_NAM,
                    gm.GLOCAL_NAM,
                    gm.GID_NO,
                    gm.GNATION
                FROM GDWUUKT.ORDER_MT om
                LEFT JOIN GDWUUKT.GUEST_MT gm ON om.ORDER_NO = gm.ORDER_NO
                WHERE TRUNC(om.CIN_DATE) = TRUNC(SYSDATE)
                AND om.STATUS = 'I'
                AND ROWNUM <= 10
            `;

            const result = await conn.execute(todayQuery);

            console.log('欄位:', result.metaData.map(m => m.name).join(', '));
            console.log('\n今日已入住訂單樣本:');

            result.rows.forEach((row, idx) => {
                const data = {};
                result.metaData.forEach((meta, i) => {
                    data[meta.name] = row[i];
                });
                console.log(`\n--- 訂單 ${idx + 1} ---`);
                console.log(JSON.stringify(data, null, 2));
            });

        } catch (err) {
            console.log('查詢失敗:', err.message);
        }

    } catch (err) {
        console.error('連線失敗:', err.message);
    } finally {
        if (conn) {
            await conn.close();
        }
    }

    console.log('\n\n✅ 搜尋完成！');
    console.log('請比對上方資料與您掃描的真實姓名，找出對應欄位。');
}

findGuestNameColumns().catch(console.error);
