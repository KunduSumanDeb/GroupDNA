# Changelog

## Unreleased

### Added
- Completed repository documentation for the project overview, workflow, and task tracking.

### Improved
- Organized the analysis pipeline into a clear notebook sequence from parsing to final reporting.

## Version 0.1.0 - Initial Analytics Pipeline

### Added
- WhatsApp chat parsing with support for multiline messages.
- Detection of system messages, media messages, and deleted messages.
- Timestamp normalization and basic parser validation.
- Export of parsed chat data to pickle files for downstream analysis.
- Group overview statistics such as active participants, timeline, and message totals.
- Busiest day and busiest hour analysis.
- Activity heatmap generation across weekdays and hours.
- Top-word extraction and meaningful text analysis.
- Response-time and silent-streak analysis.
- Personality archetype detection for group members.
- A consolidated final report notebook that combines the results of the full workflow.