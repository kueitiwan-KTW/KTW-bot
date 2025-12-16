const oracledb = require('oracledb');
require('dotenv').config();

async function run() {
    oracledb.initOracleClient();
    const conn = await oracledb.getConnection({
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        connectString: process.env.DB_CONNECT_STRING
    });

    console.log('=== WRS_ROOM_PRICE 查詢 ST房型價格 (含產品編號) ===');
    const r = await conn.execute(`
        SELECT CI_DAT, TRIM(ROOM_COD), PAY_TOT, DAYS, PRODUCT_NOS
        FROM GDWUUKT.WRS_ROOM_PRICE 
        WHERE TRIM(ROOM_COD) = 'ST' 
        AND DAYS = 1 
        AND CI_DAT >= TO_DATE('2025-12-15', 'YYYY-MM-DD')
        AND CI_DAT <= TO_DATE('2025-12-21', 'YYYY-MM-DD')
        ORDER BY CI_DAT, PAY_TOT
    `);

    console.log('CI_DAT | ROOM_COD | PAY_TOT | DAYS | PRODUCT_NOS');
    r.rows.forEach(x => {
        const d = x[0] ? x[0].toISOString().split('T')[0] : '';
        console.log(d + ' | ' + x[1] + ' | NT$' + x[2] + ' | ' + x[3] + ' | ' + (x[4] || '').trim());
    });

    await conn.close();
}

run().catch(e => console.error(e.message));
