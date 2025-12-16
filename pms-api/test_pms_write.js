/**
 * PMS 資料庫寫入測試腳本
 * 測試 Oracle PMS 是否有寫入權限
 * 
 * 測試方法：嘗試在測試表中插入/刪除一筆資料
 * 或檢查 Oracle 用戶權限
 */

const oracledb = require('oracledb');
require('dotenv').config({ path: '../.env' });

// Oracle 設定
oracledb.initOracleClient({ libDir: process.env.ORACLE_LIB_DIR || '/opt/homebrew/lib' });
oracledb.outFormat = oracledb.OUT_FORMAT_OBJECT;

async function testWritePermission() {
    let connection;

    try {
        console.log('🔌 連接 PMS 資料庫...');

        connection = await oracledb.getConnection({
            user: process.env.ORACLE_USER || 'GDWUUKT',
            password: process.env.ORACLE_PASSWORD,
            connectString: process.env.ORACLE_CONNECTION_STRING || '192.168.8.3:1521/ORCL'
        });

        console.log('✅ 資料庫連接成功！\n');

        // 測試 1: 檢查用戶權限
        console.log('📋 測試 1: 檢查用戶權限...');
        try {
            const privResult = await connection.execute(`
                SELECT PRIVILEGE 
                FROM USER_SYS_PRIVS 
                WHERE PRIVILEGE IN ('INSERT ANY TABLE', 'UPDATE ANY TABLE', 'DELETE ANY TABLE', 'CREATE TABLE')
            `);

            if (privResult.rows.length > 0) {
                console.log('   系統權限：');
                privResult.rows.forEach(row => {
                    console.log(`   ✓ ${row.PRIVILEGE}`);
                });
            } else {
                console.log('   未找到系統級寫入權限');
            }
        } catch (err) {
            console.log(`   ⚠️ 無法查詢系統權限：${err.message}`);
        }

        // 測試 2: 檢查對 ORDER_MN 表的權限
        console.log('\n📋 測試 2: 檢查 ORDER_MN 表權限...');
        try {
            const tabPrivResult = await connection.execute(`
                SELECT PRIVILEGE 
                FROM USER_TAB_PRIVS 
                WHERE TABLE_NAME = 'ORDER_MN'
            `);

            if (tabPrivResult.rows.length > 0) {
                console.log('   ORDER_MN 表權限：');
                tabPrivResult.rows.forEach(row => {
                    console.log(`   ✓ ${row.PRIVILEGE}`);
                });
            } else {
                console.log('   未找到對 ORDER_MN 的明確權限（可能使用 Schema 擁有者權限）');
            }
        } catch (err) {
            console.log(`   ⚠️ 無法查詢表權限：${err.message}`);
        }

        // 測試 3: 嘗試簡單的寫入操作（使用 DUAL 表測試語法）
        console.log('\n📋 測試 3: 測試寫入語法...');
        try {
            // 取得目前最大 IKEY 值（用於了解編號格式）
            const maxKeyResult = await connection.execute(`
                SELECT MAX(TRIM(IKEY)) as max_ikey 
                FROM GDWUUKT.ORDER_MN
            `);
            console.log(`   目前最大訂單號：${maxKeyResult.rows[0]?.MAX_IKEY || 'N/A'}`);

            // 查看訂單表結構
            console.log('\n📋 測試 4: 查看 ORDER_MN 必填欄位...');
            const colsResult = await connection.execute(`
                SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
                FROM ALL_TAB_COLUMNS 
                WHERE OWNER = 'GDWUUKT' 
                AND TABLE_NAME = 'ORDER_MN'
                AND NULLABLE = 'N'
                ORDER BY COLUMN_ID
            `);

            console.log('   必填欄位（NOT NULL）：');
            colsResult.rows.forEach(row => {
                console.log(`   • ${row.COLUMN_NAME} (${row.DATA_TYPE})${row.DATA_DEFAULT ? ' [有預設值]' : ''}`);
            });

        } catch (err) {
            console.log(`   ⚠️ 查詢失敗：${err.message}`);
        }

        // 測試 4: 實際嘗試 INSERT（但使用 ROLLBACK 回滾，不實際寫入）
        console.log('\n📋 測試 5: 嘗試 INSERT 操作（會立即 ROLLBACK）...');
        try {
            // 生成測試訂單號
            const testOrderId = 'TEST99999';

            // 嘗試插入（最小必要欄位）
            await connection.execute(`
                INSERT INTO GDWUUKT.ORDER_MN (IKEY, CI_DAT, CO_DAT, ORDER_STA, CUST_NAM)
                VALUES (:ikey, SYSDATE, SYSDATE+1, 'N', 'TEST_WRITE_PERMISSION')
            `, { ikey: testOrderId });

            console.log('   ✅ INSERT 成功！有寫入權限！');

            // 立即回滾
            await connection.rollback();
            console.log('   ↩️ 已執行 ROLLBACK，未留下測試資料');

        } catch (err) {
            if (err.message.includes('ORA-01031')) {
                console.log('   ❌ 無寫入權限 (ORA-01031: insufficient privileges)');
            } else if (err.message.includes('ORA-00942')) {
                console.log('   ❌ 無法存取表 (ORA-00942: table or view does not exist)');
            } else {
                console.log(`   ⚠️ INSERT 失敗：${err.message}`);
                // 如果是其他錯誤（如欄位缺失），可能表示有權限但語法不對
                if (!err.message.includes('privilege')) {
                    console.log('   💡 錯誤非權限相關，可能有寫入權限但需調整 SQL 語法');
                }
            }
        }

        console.log('\n' + '='.repeat(50));
        console.log('📊 測試完成！');
        console.log('='.repeat(50));

    } catch (err) {
        console.error('❌ 測試失敗：', err.message);
    } finally {
        if (connection) {
            await connection.close();
            console.log('\n🔌 資料庫連接已關閉');
        }
    }
}

// 執行測試
testWritePermission();
