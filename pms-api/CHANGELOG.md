# Changelog

## [1.6] - 2025-12-11

### Added
- **Windows Service Support**: Added `install_service.js`, `uninstall_service.js` and `manage-service.bat` for running the API as a background Windows Service using `node-windows` or `NSSM`.
- **Service Management Script**: Created `manage-service.bat` for easy Start/Stop/Restart/Status management.

### Fixed
- **Oracle Connectivity**: Resolved critical `ORA-12170: TNS: Connect timeout occurred` error by identifying and fixing `ORACLE_HOME` environment variable conflict and `listener.ora` SID configuration.
- **Firewall Issues**: Documented and resolved Windows Firewall blocking port 3000, allowing external access to the API.

### Changed
- **Installation Process**: Improved installation scripts to be more robust and user-friendly.

## [1.0.0] - 2025-12-10
- Initial Release of PMS REST API for Oracle Database.
- Endpoints for Booking search and Room availability.
