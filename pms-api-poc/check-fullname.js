/**
 * 檢查 RSORDER_MN.FULL_NAM 欄位
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

async function checkFullName() {
    console.log('🔍 檢查 RSORDER_MN.FULL_NAM 欄位...\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 1. 先看這個表的結構
        console.log('========== RSORDER_MN 資料表結構 ==========\n');
        const struct = await conn.execute('SELECT * FROM GDWUUKT.RSORDER_MN WHERE ROWNUM=1');
        console.log('欄位：', struct.metaData.map(m => m.name).join(', '));

        // 2. 搜尋是否有今日資料
        console.log('\n\n========== 今日 RSORDER_MN 資料 ==========\n');
        const today = await conn.execute(`
            SELECT * FROM GDWUUKT.RSORDER_MN 
            WHERE TRUNC(RSV_DATE) = TRUNC(SYSDATE)
            OR TRUNC(INS_DAT) = TRUNC(SYSDATE)
        `);

        console.log(`找到 ${today.rows.length} 筆今日資料`);

        if (today.rows.length > 0) {
            today.rows.forEach((row, idx) => {
                const data = {};
                today.metaData.forEach((meta, i) => {
                    data[meta.name] = row[i];
                });
                console.log(`\n--- 資料 ${idx + 1} ---`);
                console.log(JSON.stringify(data, null, 2));
            });
        }

        // 3. 搜尋是否有「洪榮宏」
        console.log('\n\n========== 搜尋「洪榮宏」==========\n');
        const search = await conn.execute(`
            SELECT * FROM GDWUUKT.RSORDER_MN 
            WHERE FULL_NAM LIKE '%洪榮宏%'
        `);

        if (search.rows.length > 0) {
            console.log('🎯 找到了！');
            search.rows.forEach((row, idx) => {
                const data = {};
                search.metaData.forEach((meta, i) => {
                    data[meta.name] = row[i];
                });
                console.log(JSON.stringify(data, null, 2));
            });
        } else {
            console.log('❌ RSORDER_MN 中沒有「洪榮宏」');
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

checkFullName().catch(console.error);
