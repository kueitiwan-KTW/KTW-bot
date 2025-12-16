const oracledb = require('oracledb');
require('dotenv').config();

async function run() {
    oracledb.initOracleClient();
    const conn = await oracledb.getConnection({
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        connectString: process.env.DB_CONNECT_STRING
    });

    console.log('=== 訂單 00709801 姓名欄位檢查 ===');
    const r = await conn.execute(`
        SELECT 
            TRIM(IKEY) as ikey,
            GALT_NAM,
            GLAST_NAM,
            GFIRST_NAM,
            CUST_NAM,
            LENGTH(GALT_NAM) as alt_len,
            LENGTH(GLAST_NAM) as last_len,
            LENGTH(GFIRST_NAM) as first_len
        FROM GDWUUKT.ORDER_MN 
        WHERE TRIM(IKEY) = '00709801'
    `);

    if (r.rows.length > 0) {
        const row = r.rows[0];
        console.log('IKEY:', row[0]);
        console.log('GALT_NAM:', JSON.stringify(row[1]), `(length: ${row[5]})`);
        console.log('GLAST_NAM:', JSON.stringify(row[2]), `(length: ${row[6]})`);
        console.log('GFIRST_NAM:', JSON.stringify(row[3]), `(length: ${row[7]})`);
        console.log('CUST_NAM:', JSON.stringify(row[4]));

        console.log('\n=== CASE WHEN 測試 ===');
        const testCase = await conn.execute(`
            SELECT 
                CASE 
                    WHEN TRIM(GALT_NAM) IS NOT NULL AND TRIM(GALT_NAM) != '' THEN TRIM(GALT_NAM)
                    WHEN TRIM(GLAST_NAM) IS NOT NULL OR TRIM(GFIRST_NAM) IS NOT NULL THEN TRIM(NVL(GLAST_NAM,'') || NVL(GFIRST_NAM,''))
                    ELSE CUST_NAM
                END as result
            FROM GDWUUKT.ORDER_MN 
            WHERE TRIM(IKEY) = '00709801'
        `);
        console.log('CASE WHEN 結果:', testCase.rows[0][0]);
    } else {
        console.log('查無此訂單');
    }

    await conn.close();
}

run().catch(e => console.error(e.message));
