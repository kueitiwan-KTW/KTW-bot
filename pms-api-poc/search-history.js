/**
 * 搜尋歷史記錄資料表
 * 郭可驥可能之前就來過，備註在歷史記錄中
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const ID_NO = 'A123182837';
const NAME = '郭可驥';

async function searchHistory() {
    console.log('🔍 搜尋歷史記錄資料表...\n');
    console.log(`搜尋條件：身分證 ${ID_NO} 或 姓名 ${NAME}\n`);
    console.log('='.repeat(80) + '\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 列出所有歷史/日誌相關資料表
        console.log('列出歷史記錄相關資料表...\n');
        const tables = await conn.execute(`
            SELECT table_name 
            FROM all_tables 
            WHERE owner = 'GDWUUKT' 
            AND (table_name LIKE '%HIST%' 
                 OR table_name LIKE '%DAILY%'
                 OR table_name LIKE '%LOG%'
                 OR table_name LIKE '%YEAR%'
                 OR table_name LIKE '%ARCHIVE%'
                 OR table_name LIKE '%OLD%')
            ORDER BY table_name
        `);

        const tableList = tables.rows.map(r => r[0]);
        console.log(`找到 ${tableList.length} 個歷史相關資料表：`);
        tableList.forEach(t => console.log(`  - ${t}`));
        console.log('\n' + '='.repeat(80) + '\n');

        let foundCount = 0;

        for (const table of tableList) {
            try {
                const struct = await conn.execute(`SELECT * FROM GDWUUKT.${table} WHERE ROWNUM=1`);
                const cols = struct.metaData.map(m => m.name);

                const idCols = cols.filter(c => c.includes('ID_COD') || c.includes('ID_NOS'));
                const nameCols = cols.filter(c => c.includes('NAM') || c.includes('NAME'));
                const remarkCols = cols.filter(c => c.includes('REMARK') || c.includes('RMK') || c.includes('MEMO') || c.includes('NOTE'));

                if (idCols.length > 0 || nameCols.length > 0) {
                    console.log(`\n檢查 ${table}...`);

                    // 用 ID 搜尋
                    for (const idCol of idCols) {
                        try {
                            const query = `SELECT * FROM GDWUUKT.${table} WHERE TRIM(${idCol}) = :id`;
                            const result = await conn.execute(query, [ID_NO]);

                            if (result.rows.length > 0) {
                                foundCount++;
                                console.log(`\n🎯 在 ${table}.${idCol} 找到 ${result.rows.length} 筆歷史記錄！\n`);

                                // 顯示所有記錄
                                result.rows.forEach((row, idx) => {
                                    console.log(`--- 記錄 ${idx + 1} ---`);
                                    result.metaData.forEach((meta, i) => {
                                        if (nameCols.includes(meta.name) || remarkCols.includes(meta.name) ||
                                            meta.name.includes('DAT') || meta.name.includes('IKEY')) {
                                            const value = row[i];
                                            const valueStr = value !== null ? String(value).substring(0, 300) : 'NULL';
                                            const highlight = (valueStr.includes('副院長') || valueStr.includes('教授')) ? ' ⭐⭐⭐ 找到了！' : '';
                                            console.log(`  ${meta.name}: ${valueStr}${highlight}`);
                                        }
                                    });
                                    console.log('');
                                });
                            }
                        } catch (err) {
                            // 忽略
                        }
                    }

                    // 用姓名搜尋
                    for (const nameCol of nameCols) {
                        try {
                            const query = `SELECT * FROM GDWUUKT.${table} WHERE ${nameCol} LIKE :name`;
                            const result = await conn.execute(query, [`%${NAME}%`]);

                            if (result.rows.length > 0) {
                                foundCount++;
                                console.log(`\n🎯 在 ${table}.${nameCol} 找到 ${result.rows.length} 筆記錄！\n`);

                                result.rows.forEach((row, idx) => {
                                    console.log(`--- 記錄 ${idx + 1} ---`);
                                    result.metaData.forEach((meta, i) => {
                                        if (nameCols.includes(meta.name) || remarkCols.includes(meta.name) ||
                                            meta.name.includes('DAT') || meta.name.includes('IKEY')) {
                                            const value = row[i];
                                            const valueStr = value !== null ? String(value).substring(0, 300) : 'NULL';
                                            const highlight = (valueStr.includes('副院長') || valueStr.includes('教授')) ? ' ⭐⭐⭐ 找到了！' : '';
                                            console.log(`  ${meta.name}: ${valueStr}${highlight}`);
                                        }
                                    });
                                    console.log('');
                                });
                            }
                        } catch (err) {
                            // 忽略
                        }
                    }
                }
            } catch (err) {
                // 忽略
            }
        }

        console.log('='.repeat(80));
        console.log(`\n搜尋完成！共找到 ${foundCount} 個地方有歷史記錄`);

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

searchHistory().catch(console.error);
