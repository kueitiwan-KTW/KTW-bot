/**
 * 深度搜尋：找出「副院長的教授」備註存在哪裡
 * 用身分證 A123182837 或姓名「郭可驥」搜尋所有可能的資料表
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const ID_NO = 'A123182837';
const NAME = '郭可驥';

async function deepSearchRemarks() {
    console.log('🔍 深度搜尋：尋找「副院長的教授」備註...\n');
    console.log(`搜尋條件：身分證 ${ID_NO} 或 姓名 ${NAME}\n`);
    console.log('='.repeat(80) + '\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 1. 列出所有可能包含客戶備註的資料表
        console.log('步驟 1：列出所有可能的資料表...\n');
        const tables = await conn.execute(`
            SELECT table_name 
            FROM all_tables 
            WHERE owner = 'GDWUUKT' 
            AND (table_name LIKE '%CUST%' 
                 OR table_name LIKE '%GUEST%'
                 OR table_name LIKE '%REMARK%'
                 OR table_name LIKE '%NOTE%'
                 OR table_name LIKE '%MEMO%'
                 OR table_name LIKE '%COMMENT%')
            ORDER BY table_name
        `);

        const tableList = tables.rows.map(r => r[0]);
        console.log(`找到 ${tableList.length} 個相關資料表\n`);

        // 2. 在每個資料表中搜尋身分證號或姓名
        let foundCount = 0;

        for (const table of tableList) {
            try {
                // 取得資料表結構
                const struct = await conn.execute(`SELECT * FROM GDWUUKT.${table} WHERE ROWNUM=1`);
                const cols = struct.metaData.map(m => m.name);

                // 找出可能的 ID 欄位
                const idCols = cols.filter(c =>
                    c.includes('ID_COD') || c.includes('ID_NOS') || c === 'ID_NO'
                );

                // 找出可能的姓名欄位
                const nameCols = cols.filter(c =>
                    c.includes('NAM') || c.includes('NAME')
                );

                // 找出可能的備註欄位
                const remarkCols = cols.filter(c =>
                    c.includes('REMARK') || c.includes('NOTE') || c.includes('MEMO') || c.includes('COMMENT') || c.includes('RMK')
                );

                if ((idCols.length > 0 || nameCols.length > 0) && remarkCols.length > 0) {
                    // 這個表有 ID/姓名 + 備註欄位，值得搜尋
                    console.log(`\n檢查 ${table}...`);
                    console.log(`  ID欄位: ${idCols.join(', ') || '無'}`);
                    console.log(`  姓名欄位: ${nameCols.join(', ') || '無'}`);
                    console.log(`  備註欄位: ${remarkCols.join(', ')}`);

                    // 先用 ID 搜尋
                    for (const idCol of idCols) {
                        try {
                            const query = `SELECT * FROM GDWUUKT.${table} WHERE TRIM(${idCol}) = :id`;
                            const result = await conn.execute(query, [ID_NO]);

                            if (result.rows.length > 0) {
                                foundCount++;
                                console.log(`\n  🎯 在 ${table}.${idCol} 找到資料！`);

                                // 顯示所有備註欄位和姓名欄位
                                result.metaData.forEach((meta, idx) => {
                                    if (remarkCols.includes(meta.name) || nameCols.includes(meta.name)) {
                                        const value = result.rows[0][idx];
                                        const valueStr = value !== null ? String(value).substring(0, 300) : 'NULL';
                                        const highlight = (valueStr.includes('副院長') || valueStr.includes('教授')) ? ' ⭐⭐⭐ 找到了！' : '';
                                        console.log(`    ${meta.name}: ${valueStr}${highlight}`);
                                    }
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
                                console.log(`\n  🎯 在 ${table}.${nameCol} 找到資料！`);

                                result.metaData.forEach((meta, idx) => {
                                    if (remarkCols.includes(meta.name) || nameCols.includes(meta.name)) {
                                        const value = result.rows[0][idx];
                                        const valueStr = value !== null ? String(value).substring(0, 300) : 'NULL';
                                        const highlight = (valueStr.includes('副院長') || valueStr.includes('教授')) ? ' ⭐⭐⭐ 找到了！' : '';
                                        console.log(`    ${meta.name}: ${valueStr}${highlight}`);
                                    }
                                });
                            }
                        } catch (err) {
                            // 忽略
                        }
                    }
                }
            } catch (err) {
                // console.log(`  ❌ ${table}: ${err.message.split('\n')[0]}`);
            }
        }

        console.log('\n' + '='.repeat(80));
        console.log(`\n搜尋完成！共在 ${foundCount} 個地方找到相關資料`);

        if (foundCount === 0) {
            console.log('\n❌ 在所有資料表中都找不到「副院長」或「教授」備註');
            console.log('\n可能原因：');
            console.log('  1. 備註尚未輸入到 PMS 資料庫');
            console.log('  2. 備註在我沒權限存取的資料表');
            console.log('  3. 備註欄位名稱不在搜尋範圍內');
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

deepSearchRemarks().catch(console.error);
