/**
 * 深度搜尋：尋找「洪榮宏」和 FULL 相關欄位
 */

require('dotenv').config();
const oracledb = require('oracledb');

// 初始化 Oracle Thick 模式
try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const SEARCH_NAME = '洪榮宏';
const ROOM_NO = '606';

async function deepSearch() {
    console.log(`🔍 深度搜尋：房間 ${ROOM_NO} 中包含「${SEARCH_NAME}」的欄位...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });
        console.log('✅ 資料庫連線成功\n');

        // 1. 搜尋所有包含 FULL 的欄位名
        console.log('========== 步驟 1: 搜尋包含 FULL 的欄位 ==========\n');
        const fullCols = await conn.execute(`
            SELECT table_name, column_name 
            FROM all_tab_columns 
            WHERE owner = 'GDWUUKT' 
            AND column_name LIKE '%FULL%'
        `);

        if (fullCols.rows.length > 0) {
            console.log('找到以下包含 FULL 的欄位：');
            fullCols.rows.forEach(row => {
                console.log(`  ${row[0]}.${row[1]}`);
            });
        } else {
            console.log('❌ 沒有找到包含 FULL 的欄位名');
        }

        // 2. 檢查 ASSIGN_DT (房間分配表) 所有欄位
        console.log('\n\n========== 步驟 2: ASSIGN_DT 房間分配表 (606房) ==========\n');
        const assignQuery = `
            SELECT * FROM GDWUUKT.ASSIGN_DT 
            WHERE TRIM(ROOM_NOS) = :room 
            AND ROWNUM = 1
        `;
        const assignResult = await conn.execute(assignQuery, [ROOM_NO]);

        if (assignResult.rows.length > 0) {
            console.log('ASSIGN_DT 所有欄位：');
            assignResult.metaData.forEach((meta, idx) => {
                const value = assignResult.rows[0][idx];
                const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐ 找到了！' : '';
                console.log(`  ${meta.name}: ${valueStr}${highlight}`);
            });
        } else {
            console.log(`❌ ASSIGN_DT 中找不到房號 ${ROOM_NO}`);
        }

        // 3. 搜尋所有與 606 房相關的資料表
        console.log('\n\n========== 步驟 3: 搜尋所有提到房號 606 的資料 ==========\n');

        // 列出可能的資料表
        const tables = ['ORDER_MN', 'ORDER_DT', 'ASSIGN_DT', 'ROOM_STA_DT'];

        for (const table of tables) {
            try {
                // 先取得欄位結構
                const struct = await conn.execute(`SELECT * FROM GDWUUKT.${table} WHERE ROWNUM=1`);
                const roomCols = struct.metaData.filter(m =>
                    m.name.includes('ROOM') || m.name.includes('NOS')
                );

                if (roomCols.length > 0) {
                    // 嘗試用每個可能的房號欄位搜尋
                    for (const col of roomCols) {
                        try {
                            const query = `
                                SELECT * FROM GDWUUKT.${table} 
                                WHERE TRIM(${col.name}) = :room
                            `;
                            const result = await conn.execute(query, [ROOM_NO]);

                            if (result.rows.length > 0) {
                                console.log(`\n📋 ${table} (透過 ${col.name} = ${ROOM_NO}):`);
                                result.metaData.forEach((meta, idx) => {
                                    const value = result.rows[0][idx];
                                    const valueStr = value !== null ? String(value).substring(0, 80) : 'NULL';
                                    const highlight = valueStr.includes(SEARCH_NAME) ? ' ⭐⭐⭐' : '';
                                    if (meta.name.includes('NAM') || meta.name.includes('NAME') || highlight) {
                                        console.log(`  ${meta.name}: ${valueStr}${highlight}`);
                                    }
                                });
                            }
                        } catch (err) {
                            // 忽略查詢錯誤（欄位類型不符等）
                        }
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

    console.log('\n\n✅ 深度搜尋完成！');
}

deepSearch().catch(console.error);
