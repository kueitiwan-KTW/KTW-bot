/**
 * 列出所有 GUEST/REGIST 相關資料表並搜尋身分證號
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const ID_NO = 'M122076214';

async function findIDColumn() {
    console.log(`🔍 搜尋包含身分證號 ${ID_NO} 的資料表...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 1. 列出所有 GUEST/REGIST 相關資料表
        console.log('========== 列出所有 GUEST/REGIST 相關資料表 ==========\n');
        const tables = await conn.execute(`
            SELECT table_name 
            FROM all_tables 
            WHERE owner = 'GDWUUKT' 
            AND (table_name LIKE '%GUEST%' 
                 OR table_name LIKE '%REGIST%' 
                 OR table_name LIKE '%CHECKIN%'
                 OR table_name LIKE '%CHECK%')
            ORDER BY table_name
        `);

        const tableList = tables.rows.map(r => r[0]);
        console.log(`找到 ${tableList.length} 個資料表：`);
        tableList.forEach(t => console.log(`  - ${t}`));

        // 2. 在每個資料表中搜尋身分證號
        console.log('\n\n========== 搜尋身分證號 ==========\n');

        for (const table of tableList) {
            try {
                // 取得資料表結構
                const struct = await conn.execute(`SELECT * FROM GDWUUKT.${table} WHERE ROWNUM=1`);
                const cols = struct.metaData.map(m => m.name);

                // 找出可能存放 ID 的欄位
                const idCols = cols.filter(c =>
                    c.includes('ID') ||
                    c.includes('NOS') ||
                    c.includes('NUM') ||
                    c === 'GID_NO'
                );

                if (idCols.length > 0) {
                    console.log(`\n檢查 ${table} (ID欄位: ${idCols.join(', ')})...`);

                    for (const col of idCols) {
                        try {
                            const query = `SELECT * FROM GDWUUKT.${table} WHERE TRIM(${col}) = :id`;
                            const result = await conn.execute(query, [ID_NO]);

                            if (result.rows.length > 0) {
                                console.log(`\n🎯🎯🎯 找到了！在 ${table}.${col} 🎯🎯🎯\n`);
                                console.log('所有欄位：');
                                result.metaData.forEach((meta, idx) => {
                                    const value = result.rows[0][idx];
                                    const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                                    const highlight = (meta.name.includes('NAM') || meta.name.includes('NAME') || meta.name.includes('FULL')) ? ' ⭐⭐⭐' : '';
                                    console.log(`  ${meta.name}${highlight}: ${valueStr}`);
                                });
                                console.log('\n' + '='.repeat(80) + '\n');
                            }
                        } catch (err) {
                            // 忽略類型錯誤等
                        }
                    }
                }
            } catch (err) {
                console.log(`  ❌ ${table}: ${err.message.split('\n')[0]}`);
            }
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }

    console.log('\n✅ 搜尋完成！');
}

findIDColumn().catch(console.error);
