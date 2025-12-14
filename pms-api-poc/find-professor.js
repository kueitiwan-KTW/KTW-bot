/**
 * 查詢身分證 A123182837 的所有欄位
 */

require('dotenv').config();
const oracledb = require('oracledb');

try {
    oracledb.initOracleClient({ libDir: process.env.ORACLE_CLIENT_LIB_DIR });
} catch (err) { }

const ID_NO = 'A123182837';

async function findProfessor() {
    console.log(`🔍 查詢身分證 ${ID_NO} 的所有欄位...\n`);

    let conn;
    try {
        conn = await oracledb.getConnection({
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            connectString: process.env.DB_CONNECT_STRING
        });

        const query = `SELECT * FROM GDWUUKT.GUEST_MN WHERE TRIM(ID_COD) = :id`;
        const result = await conn.execute(query, [ID_NO]);

        if (result.rows.length > 0) {
            console.log('🎯 找到了！所有欄位：\n');
            result.metaData.forEach((meta, idx) => {
                const value = result.rows[0][idx];
                const valueStr = value !== null ? String(value).substring(0, 200) : 'NULL';
                const highlight = (meta.name.includes('REMARK') || meta.name.includes('NAM') || meta.name.includes('NAME')) ? ' ⭐' : '';
                console.log(`${meta.name}${highlight}: ${valueStr}`);
            });
        } else {
            console.log('❌ 找不到此身分證號');
        }

        await conn.close();

    } catch (err) {
        console.error('錯誤:', err.message);
    }
}

findProfessor().catch(console.error);
