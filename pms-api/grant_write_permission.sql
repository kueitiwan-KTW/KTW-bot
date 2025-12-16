-- grant_write_permission.sql
-- Grant INSERT/UPDATE permissions to GDWUUKT for same-day booking feature
-- Run as SYS or SYSTEM user

-- Grant INSERT permission on ORDER_MN (order master table)
GRANT INSERT ON GDWUUKT.ORDER_MN TO GDWUUKT;

-- Grant INSERT permission on ORDER_DT (order detail table)  
GRANT INSERT ON GDWUUKT.ORDER_DT TO GDWUUKT;

-- Grant UPDATE permission on ORDER_MN (for status updates)
GRANT UPDATE ON GDWUUKT.ORDER_MN TO GDWUUKT;

-- Verify permissions
SELECT GRANTEE, TABLE_NAME, PRIVILEGE 
FROM DBA_TAB_PRIVS 
WHERE GRANTEE = 'GDWUUKT' 
AND TABLE_NAME IN ('ORDER_MN', 'ORDER_DT');

EXIT;
