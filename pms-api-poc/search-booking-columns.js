/**
 * 搜尋特定訂單的所有欄位
 * 目標：找到包含 "洪榮宏" 的欄位
 */

require('dotenv').config();
const oracledb = require('oracledb');

const BOOKING_ID = '00708801';
const SEARCH_NAME = '洪榮宏';

async function searchAllColumns() {
    console.log(`🔍 搜尋訂單 ${BOOKING_ID} 中包含 "${SEARCH_NAME}" 的欄位...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            connectString: process.env.DB_CONNECT_STRING,
            externalAuth: true
        });
        console.log('✅ 資料庫連線成功\n');

        // 查詢所有相關資料表
        const tables = [
            { name: 'ORDER_MT', key: 'ORDER_NO' },
            { name: 'ORDER_DT', key: 'ORDER_NO' },
            { name: 'GUEST_MT', key: 'ORDER_NO' },
            { name: 'GUEST_DT', key: 'ORDER_NO' },
        ];

        for (const table of tables) {
            try {
                const query = `SELECT * FROM GDWUUKT.${table.name} WHERE ${table.key} = :id`;
                const result = await conn.execute(query, [BOOKING_ID]);

                if (result.rows && result.rows.length > 0) {
                    console.log(`\n📋 ${table.name} (${result.rows.length} 筆)`);

                    result.rows.forEach((row, rowIdx) => {
                        console.log(`\n--- 第 ${rowIdx + 1} 筆 ---`);
                        result.metaData.forEach((meta, colIdx) => {
                            const value = row[colIdx];
                            const valueStr = value !== null ? String(value) : '';
                            const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐ 找到了！' : '';
                            console.log(`  ${meta.name}: ${valueStr}${highlight}`);
                        });
                    });
                } else {
                    console.log(`\n❌ ${table.name}: 無資料`);
                }
            } catch (err) {
                console.log(`\n❌ ${table.name}: ${err.message.split('\n')[0]}`);
            }
        }

    } catch (err) {
        console.error('連線失敗:', err.message);
    } finally {
        if (conn) {
            await conn.close();
        }
    }

    console.log('\n\n✅ 搜尋完成！');
}

searchAllColumns().catch(console.error);
