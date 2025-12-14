/**
 * 用身分證號搜尋洪榮宏的資料
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const ID_NO = 'M122076214';

async function searchByID() {
    console.log(`🔍 用身分證號 ${ID_NO} 搜尋所有資料...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 搜尋所有可能的資料表
        const tables = ['ORDER_MN', 'RSORDER_MN', 'ASSIGN_DT', 'CUST_MT'];

        for (const table of tables) {
            try {
                console.log(`\n========== ${table} ==========\n`);

                // 先取得資料表結構
                const struct = await conn.execute(`SELECT * FROM GDWUUKT.${table} WHERE ROWNUM=1`);
                const idCols = struct.metaData.filter(m =>
                    m.name.includes('ID') || m.name.includes('NOS')
                );

                console.log(`ID 相關欄位: ${idCols.map(c => c.name).join(', ')}`);

                // 用每個可能的 ID 欄位搜尋
                for (const col of idCols) {
                    try {
                        const query = `SELECT * FROM GDWUUKT.${table} WHERE ${col.name} = :id`;
                        const result = await conn.execute(query, [ID_NO]);

                        if (result.rows.length > 0) {
                            console.log(`\n🎯 在 ${table}.${col.name} 找到了！\n`);
                            result.metaData.forEach((meta, idx) => {
                                const value = result.rows[0][idx];
                                const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                                const highlight = (meta.name.includes('NAM') || meta.name.includes('NAME')) ? ' 📛' : '';
                                console.log(`${meta.name}${highlight}: ${valueStr}`);
                            });
                        }
                    } catch (err) {
                        // 忽略類型不符等錯誤
                    }
                }

            } catch (err) {
                console.log(`❌ ${table}: ${err.message.split('\n')[0]}`);
            }
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }

    console.log('\n\n✅ 搜尋完成！');
}

searchByID().catch(console.error);
