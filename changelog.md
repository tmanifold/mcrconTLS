# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2017-05-12
### Added
- This changelog
- send and receive methods for the MCRCONTLSServer class
### Changed
- Moved connect() implememtation to MCRCONTLSClient
    - How the connection is initiatied should be the responsibility of the client. This change removes functionality from the shared McRconTLS class that can't be used by the server
- MCRCONTLSServer can now handle connections from multiple clients


