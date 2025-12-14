/**
 * 在 RSORDER_MN 中搜尋訂單或房號關聯
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

async function searchRSOrder() {
    console.log('�� 在 RSORDER_MN 中搜尋與訂單/房號的關聯...\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 1. 直接搜尋「洪榮宏」
        console.log('========== 搜尋「洪榮宏」 ==========\n');
        const hongSearch = await conn.execute(`
            SELECT * FROM GDWUUKT.RSORDER_MN 
            WHERE FULL_NAM LIKE '%洪%' OR FULL_NAM LIKE '%榮%' OR FULL_NAM LIKE '%宏%'
        `);

        if (hongSearch.rows.length > 0) {
            console.log(`🎯 找到 ${hongSearch.rows.length} 筆包含「洪/榮/宏」的資料：\n`);
            hongSearch.rows.forEach((row, idx) => {
                const fullNam = row[hongSearch.metaData.findIndex(m => m.name === 'FULL_NAM')];
                const orderNos = row[hongSearch.metaData.findIndex(m => m.name === 'ORDER_NOS')];
                const rsorderNos = row[hongSearch.metaData.findIndex(m => m.name === 'RSORDER_NOS')];
                console.log(`${idx + 1}. FULL_NAM: ${fullNam}`);
                console.log(`   ORDER_NOS: ${orderNos}`);
                console.log(`   RSORDER_NOS: ${rsorderNos}\n`);
            });
        } else {
            console.log('❌ 沒有找到');
        }

        // 2. 檢查是否有 ORDER_NOS 欄位可以關聯到 ORDER_MN
        console.log('\n========== 檢查 ORDER_NOS 欄位 ==========\n');
        const orderLink = await conn.execute(`
            SELECT RSORDER_NOS, ORDER_NOS, FULL_NAM, TEL1_NOS 
            FROM GDWUUKT.RSORDER_MN 
            WHERE ORDER_NOS IS NOT NULL 
            AND ROWNUM <= 10
        `);

        console.log(`找到 ${orderLink.rows.length} 筆有 ORDER_NOS 的資料（最多顯示 10 筆）：\n`);
        orderLink.rows.forEach((row, idx) => {
            console.log(`${idx + 1}. ORDER_NOS: ${row[1]}, FULL_NAM: ${row[2]}, TEL: ${row[3]}`);
        });

        // 3. 如果 ORDER_NOS 是關聯欄位，查詢 00708801
        console.log('\n\n========== 查詢訂單 00708801 的 RSORDER_MN 資料 ==========\n');
        const orderQuery = await conn.execute(`
            SELECT * FROM GDWUUKT.RSORDER_MN 
            WHERE TRIM(ORDER_NOS) = '00708801'
        `);

        if (orderQuery.rows.length > 0) {
            console.log('🎯 找到了！訂單 00708801 的 RSORDER_MN 資料：\n');
            orderQuery.metaData.forEach((meta, idx) => {
                const value = orderQuery.rows[0][idx];
                const valueStr = value !== null ? String(value) : 'NULL';
                const highlight = meta.name === 'FULL_NAM' ? ' ⭐⭐⭐' : '';
                console.log(`${meta.name}: ${valueStr}${highlight}`);
            });
        } else {
            console.log('❌ 訂單 00708801 在 RSORDER_MN 中沒有資料');
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

searchRSOrder().catch(console.error);
