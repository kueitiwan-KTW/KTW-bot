const express = require('express');
const router = express.Router();
const oracledb = require('oracledb');

// Debug endpoint to查詢單筆訂單的所有數值欄位
router.get('/order-fields/:booking_id', async (req, res) => {
    let connection;
    try {
        connection = await oracledb.getConnection();
        const { booking_id } = req.params;

        // 查詢 ORDER_MN 的所有數值欄位
        const orderMnResult = await connection.execute(
            `SELECT 
                ORDER_DEPOSIT,
                PRECREDIT_AMT,
                CREDIT_LIMIT
             FROM GDWUUKT.ORDER_MN
             WHERE TRIM(RVRESERVE_NOS) = :booking_id OR TRIM(IKEY) = :booking_id`,
            { booking_id }
        );

        // 查詢 ORDER_DT 的 PAY_TOT
        const orderDtResult = await connection.execute(
            `SELECT 
                PAY_TOT,
                RENT_TOT,
                RENT_AMT
             FROM GDWUUKT.ORDER_DT od
             INNER JOIN GDWUUKT.ORDER_MN om ON od.IKEY = om.IKEY
             WHERE TRIM(om.RVRESERVE_NOS) = :booking_id OR TRIM(om.IKEY) = :booking_id`,
            { booking_id }
        );

        res.json({
            success: true,
            data: {
                ORDER_MN: orderMnResult.rows.length > 0 ? {
                    ORDER_DEPOSIT: orderMnResult.rows[0][0],
                    PRECREDIT_AMT: orderMnResult.rows[0][1],
                    CREDIT_LIMIT: orderMnResult.rows[0][2]
                } : null,
                ORDER_DT: orderDtResult.rows.length > 0 ? {
                    PAY_TOT: orderDtResult.rows[0][0],
                    RENT_TOT: orderDtResult.rows[0][1],
                    RENT_AMT: orderDtResult.rows[0][2]
                } : null
            }
        });
    } catch (error) {
        console.error('Debug query error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    } finally {
        if (connection) {
            try {
                await connection.close();
            } catch (err) {
                console.error('Error closing connection:', err);
            }
        }
    }
});

module.exports = router;
