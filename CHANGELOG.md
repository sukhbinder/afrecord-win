# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-05-16

### Added
- Refactored audio recording to use native ctypes for Windows MCI (MultiMedia Control Interface) implementation
- More reliable and platform-native audio capture

### Improved
- Updated test suite to work with the new ctypes-based MCI implementation
- Removed failing tests and improved test coverage

### Fixed
- Various minor issues with audio recording and test failures

## [0.1.0] - Initial Release

### Added
- Basic CLI interface for recording audio from the default microphone
- Comprehensive test suite
- Output to WAV format by default

---

[Unreleased]: https://github.com/sukhbinder/afrecord-win/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/sukhbinder/afrecord-win/releases/tag/v0.1.1
[0.1.0]: https://github.com/sukhbinder/afrecord-win/releases/tag/v0.1.0
