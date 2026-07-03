# AI Usage and Development Notes

## Project

**GroupDNA – WhatsApp Group Analyzer**

Author: Suman Deb Kundu

---

# Purpose of this Document

This document explains how Artificial Intelligence (AI) was used during the development of this project.

The objective is to maintain transparency regarding the development process while clearly stating that all implementation decisions, testing, validation, and final acceptance were performed by the project author.

---

# Development Methodology

The project was developed feature by feature rather than generating the complete project at once.

The workflow followed for almost every feature was:

1. Study the Development PDF and understand the expected functionality.
2. Discuss the algorithm before implementation.
3. Decide whether the proposed approach was appropriate or required improvement.
4. Implement one notebook cell at a time.
5. Execute and validate every cell before proceeding.
6. Review the generated outputs.
7. Modify the algorithm whenever the output was not satisfactory.
8. Export the feature output for use in the next feature.

This iterative process was followed throughout the project.

---

# AI Assistance

AI was primarily used as a development assistant.

Its responsibilities included:

- Explaining algorithms.
- Suggesting implementation approaches.
- Generating draft code.
- Reviewing logic.
- Helping debug errors.
- Improving notebook organization.
- Suggesting cleaner implementations.
- Assisting with documentation.

The AI was **not** used as a simple copy-and-paste solution.

Every generated function was executed, reviewed, tested, and analysed before it became part of the final notebook.

Whenever an implementation did not satisfy the expected behaviour, it was revised before continuing.

---

# Feature-wise AI Usage

## Features 1–6

AI assistance was mainly limited to:

- Code review
- Algorithm discussion
- Debugging
- Code refinement
- Improving readability

Most implementations followed the project development document with only minor refinements.

---

## Feature 7 (Personality Archetype Detection)

Feature 7 required significantly more discussion than the previous features.

The original Development PDF provided only the basic concepts for each archetype.

Several algorithms were redesigned or refined after analysing their practical behaviour on the dataset.

Although AI generated a considerable portion of the draft implementations for this feature, every algorithm was discussed, validated, tested, and revised before being accepted.

The final implementations therefore represent a collaborative design process rather than direct code generation.

---

# Major Improvements Beyond the Development PDF

During development, several improvements were intentionally introduced after discussion.

These include:

- Ignoring Meta AI during analysis.
- Ignoring WhatsApp system events (group name changes, joins, leaves, etc.).
- Introducing a minimum message threshold (`MIN_MESSAGES`) for reliable personality analysis.
- Using actual timestamps instead of group-level heatmaps for Night Owl detection.
- Improving Drama Queen detection using punctuation together with emotion-related keywords.
- Improving Question Master detection to recognise both formal and informal question styles.
- Adding emoji-based humour detection for The Comedian.
- Using silent streak analysis for The Ghost instead of response time.
- Applying score normalization before final personality assignment.
- Creating a consolidated Final Report feature that integrates all previous outputs.

These modifications were introduced because they produced more meaningful and explainable results while remaining consistent with the original project objectives.

---

# Validation Process

Every notebook contains:

- Validation section
- Structured outputs
- Export section

Outputs from one feature were validated before being used by subsequent features.

The complete project was executed feature-by-feature to ensure consistency across all exported files.

---

# Personal Contribution

The overall project architecture, notebook organisation, testing process, validation, execution, and final acceptance of every implementation were carried out by the project author.

Every generated function was reviewed before integration into the project.

Whenever improvements were required, they were discussed first and implemented only after understanding the algorithm and verifying the resulting outputs.

---

# Declaration

Artificial Intelligence was used as a software development assistant during this project.

The final implementation reflects the author's understanding, testing, validation, and acceptance of the algorithms included in the project.

No function was included in the final submission without being executed, reviewed, and evaluated within the complete project pipeline.