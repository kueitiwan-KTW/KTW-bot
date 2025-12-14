/**
 * 搜尋今日所有已入住訂單，尋找「洪榮宏」
 */

require('dotenv').config();
const oracledb = require('oracledb');

// 初始化 Oracle Thick 模式 (支援繁體中文字元集)
try {
    oracledb.initOracleClient({
        libDir: process.env.ORACLE_CLIENT_LIB_DIR
    });
} catch (err) {
    // 已經初始化過會拋出錯誤，忽略即可
}

const SEARCH_NAME = '洪榮宏';

async function searchTodayBookings() {
    console.log(`🔍 搜尋今日所有已入住訂單中包含「${SEARCH_NAME}」的欄位...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });
        console.log('✅ 資料庫連線成功\n');

        const query = `
            SELECT 
                TRIM(IKEY) as ORDER_NO,
                CUST_NAM, 
                GLAST_NAM, 
                GFIRST_NAM, 
                GALT_NAM, 
                ATTEN_NAM,
                SECRETARY_NAM,
                ORDER_RMK
            FROM GDWUUKT.ORDER_MN 
            WHERE TRUNC(CI_DAT) = TRUNC(SYSDATE) 
            AND ORDER_STA = 'I'
        `;

        const result = await conn.execute(query);

        console.log(`找到 ${result.rows.length} 筆今日已入住訂單\n`);
        console.log('='.repeat(80));

        let found = false;
        result.rows.forEach((row, idx) => {
            const [orderNo, custNam, gLastNam, gFirstNam, gAltNam, attenNam, secretaryNam, orderRmk] = row;

            // 檢查是否包含搜尋名稱
            const fields = {
                ORDER_NO: String(orderNo || ''),
                CUST_NAM: String(custNam || ''),
                GLAST_NAM: String(gLastNam || ''),
                GFIRST_NAM: String(gFirstNam || ''),
                GALT_NAM: String(gAltNam || ''),
                ATTEN_NAM: String(attenNam || ''),
                SECRETARY_NAM: String(secretaryNam || ''),
                ORDER_RMK: String(orderRmk || '')
            };

            const matchedFields = Object.entries(fields).filter(([key, value]) =>
                value.includes(SEARCH_NAME)
            );

            if (matchedFields.length > 0) {
                found = true;
                console.log(`\n🎯 找到了！訂單 ${idx + 1}: ${orderNo}`);
                console.log('-'.repeat(80));
                Object.entries(fields).forEach(([key, value]) => {
                    const highlight = value.includes(SEARCH_NAME) ? ' ⭐⭐⭐' : '';
                    console.log(`  ${key}: ${value}${highlight}`);
                });
                console.log('='.repeat(80));
            } else {
                console.log(`\n訂單 ${idx + 1}: ${orderNo}`);
                console.log(`  CUST_NAM: ${custNam}`);
                console.log(`  GLAST_NAM: ${gLastNam}, GFIRST_NAM: ${gFirstNam}`);
            }
        });

        if (!found) {
            console.log(`\n\n❌ 在今日所有已入住訂單中都找不到「${SEARCH_NAME}」`);
            console.log('可能原因：');
            console.log('  1. 該客人尚未掃描證件');
            console.log('  2. 證件資料存在其他資料表');
            console.log('  3. 訂單狀態不是「I」（已入住）');
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

searchTodayBookings().catch(console.error);
