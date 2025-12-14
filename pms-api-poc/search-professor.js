/**
 * 搜尋今日入住客人中包含「副院長」或「教授」的資料
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

async function searchProfessor() {
    console.log('🔍 搜尋今日入住客人中的「副院長」或「教授」...\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        // 查詢今日已入住的 GUEST_MN
        const query = `
            SELECT * FROM GDWUUKT.GUEST_MN 
            WHERE TRUNC(CI_DAT) = TRUNC(SYSDATE)
            AND GUEST_STA = 'O'
        `;

        const result = await conn.execute(query);

        console.log(`找到 ${result.rows.length} 筆今日入住客人\n`);
        console.log('='.repeat(80) + '\n');

        const keywords = ['副院長', '教授', '院長', 'professor', 'dean'];
        let found = false;

        result.rows.forEach((row, idx) => {
            const data = {};
            result.metaData.forEach((meta, i) => {
                data[meta.name] = row[i];
            });

            // 檢查所有欄位是否包含關鍵字
            const matchedFields = [];
            Object.entries(data).forEach(([key, value]) => {
                const valueStr = value !== null ? String(value) : '';
                keywords.forEach(keyword => {
                    if (valueStr.includes(keyword)) {
                        matchedFields.push({ field: key, value: valueStr, keyword });
                    }
                });
            });

            if (matchedFields.length > 0) {
                found = true;
                console.log(`🎯 找到了！客人 ${idx + 1}\n`);
                console.log('關鍵欄位：');
                console.log(`  房號: ${data.ROOM_NOS}`);
                console.log(`  訂單號: ${data.IKEY}`);
                console.log(`  訂房姓名: ${data.LAST_NAM} ${data.FIRST_NAM}`);
                console.log(`  登記姓名: ${data.ALT_NAM}`);
                console.log(`  身分證: ${data.ID_COD}`);
                console.log(`  電話: ${data.CONTACT1_RMK}`);

                console.log('\n匹配的欄位：');
                matchedFields.forEach(m => {
                    console.log(`  ${m.field}: ${m.value.substring(0, 100)} ⭐ (包含「${m.keyword}」)`);
                });

                console.log('\n所有欄位：');
                Object.entries(data).forEach(([key, value]) => {
                    const valueStr = value !== null ? String(value).substring(0, 100) : 'NULL';
                    const highlight = (key.includes('NAM') || key.includes('NAME') || key.includes('REMARK')) ? ' 📛' : '';
                    console.log(`  ${key}${highlight}: ${valueStr}`);
                });

                console.log('\n' + '='.repeat(80) + '\n');
            }
        });

        if (!found) {
            console.log('❌ 沒有找到包含「副院長」或「教授」的客人');
            console.log('\n所有今日入住客人的姓名：');
            result.rows.forEach((row, idx) => {
                const roomNos = row[result.metaData.findIndex(m => m.name === 'ROOM_NOS')];
                const altNam = row[result.metaData.findIndex(m => m.name === 'ALT_NAM')];
                const lastName = row[result.metaData.findIndex(m => m.name === 'LAST_NAM')];
                const firstName = row[result.metaData.findIndex(m => m.name === 'FIRST_NAM')];
                console.log(`  ${idx + 1}. 房號 ${roomNos}: ${lastName} ${firstName} / ${altNam}`);
            });
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }

    console.log('\n✅ 搜尋完成！');
}

searchProfessor().catch(console.error);
