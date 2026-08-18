# Changelog

All notable changes to Pyffice will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **PyfficePDF binary storage (T-NEW-159)** -- `get_binary()` no
  longer returns an empty stub. It now returns the stored
  `content["bytes"]` blob when present, or the on-disk bytes from
  `_get_bytes()` otherwise. `set_content({"file_path": ..., "bytes": ...})`
  with `location == "internal"` round-trips the binary envelope
  through a fresh `PyfficeDocument`. Unknown `location` values
  raise `UnknownLocationError`. 5 new tests in
  `tests/pyffice_unit/unit/images/test_pdf_binary.py`.

### Added

- **Palette extraction (T-NEW-117)** -- `PyfficeColorPalette.extract_palette()`
  returns ordered (color, frequency) tuples from an image's palette.
  Referenced by NchantdOffice NchantdPalette toolbar; commit `1cd3c48`
  on `origin/gamma`. Pushed via `nchantdoffice` integration as `419a317`.

## [0.1.1] - 2025-05-25

### Added
- Enhanced document processing with comprehensive format support
- Improved CLI with 72 commands across 27 modules
- Port-based architecture for extensibility
- Complete type annotation coverage
- Comprehensive test suite with 61 test files

### Changed
- Migrated from ogma/condor to kahndor for agent coordination
- Refactored imports for better organization
- Improved error handling across all modules

### Fixed
- All pylint errors (was 1,658, now 0)
- All security bandit issues (HIGH/MEDIUM/LOW)
- Document organization for release alignment

## [0.1.0] - 2025-05-01

### Added
- Initial release
- Document processing (docx, pdf, odt, md, LaTeX)
- Spreadsheet processing (xlsx, csv, ods)
- Presentation support (pptx, odp)
- Media handling (images, audio, video)
- Email integration
- Calendar management
- Database operations
- CLI interface
- Agent system
- Workflow automation
