/**
 * 列出所有今日入住客人的備註欄位
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

async function checkGuestRemarks() {
    console.log('🔍 檢查今日入住客人的備註欄位（REMARK1-4）...\n');

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        const query = `
            SELECT 
                ROOM_NOS,
                IKEY,
                LAST_NAM,
                FIRST_NAM,
                ALT_NAM,
                REMARK1,
                REMARK2,
                REMARK3,
                REMARK4,
                ID_COD,
                CONTACT1_RMK
            FROM GDWUUKT.GUEST_MN 
            WHERE TRUNC(CI_DAT) = TRUNC(SYSDATE)
            AND GUEST_STA = 'O'
            ORDER BY ROOM_NOS
        `;

        const result = await conn.execute(query);

        console.log(`找到 ${result.rows.length} 筆今日入住客人\n`);
        console.log('='.repeat(80) + '\n');

        const keywords = ['副院長', '教授', '院長', 'professor', 'dean', '副', '院', '教', '授'];

        result.rows.forEach((row, idx) => {
            const [roomNos, ikey, lastName, firstName, altNam, remark1, remark2, remark3, remark4, idCod, contact] = row;

            console.log(`${idx + 1}. 房號 ${roomNos} (訂單 ${ikey})`);
            console.log(`   訂房姓名: ${lastName} ${firstName}`);
            console.log(`   登記姓名: ${altNam}`);
            console.log(`   身分證: ${idCod}`);
            console.log(`   電話: ${contact}`);
            console.log(`   備註欄位:`);

            const remarks = [
                { name: 'REMARK1', value: remark1 },
                { name: 'REMARK2', value: remark2 },
                { name: 'REMARK3', value: remark3 },
                { name: 'REMARK4', value: remark4 }
            ];

            let foundKeyword = false;
            remarks.forEach(r => {
                const value = r.value !== null ? String(r.value) : '';
                if (value) {
                    const hasKeyword = keywords.some(kw => value.includes(kw));
                    const highlight = hasKeyword ? ' ⭐⭐⭐ 找到了！' : '';
                    console.log(`     ${r.name}: ${value.substring(0, 200)}${highlight}`);
                    if (hasKeyword) foundKeyword = true;
                } else {
                    console.log(`     ${r.name}: (空白)`);
                }
            });

            if (foundKeyword) {
                console.log('\n   🎯🎯🎯 此客人的備註中包含關鍵字！🎯🎯🎯');
            }

            console.log('\n' + '-'.repeat(80) + '\n');
        });

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }

    console.log('✅ 檢查完成！');
}

checkGuestRemarks().catch(console.error);
