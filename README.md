# GroupDNA

GroupDNA is a WhatsApp group analytics project that turns exported chat data into a structured set of insights. The repository contains a notebook-based workflow for parsing chats, analyzing interaction patterns, and generating a final report that summarizes group behavior.

## What the project does

- Parses exported WhatsApp chats into structured message data.
- Handles multiline messages, system notifications, media messages, and deleted message markers.
- Computes group-level statistics such as activity timeline and active participants.
- Identifies the busiest day and busiest hour.
- Builds an activity heatmap across weekdays and hours.
- Extracts common and meaningful words from the conversation.
- Analyzes response speed and silent streaks.
- Assigns personality archetypes to participants based on behavior.
- Produces a final consolidated report.

## Repository structure

- Development/: Jupyter notebooks for each analysis step.
- Data/: Intermediate outputs and serialized pickle files.
- Dataset/: Sample chat data used for experimentation.
- Streamlit_App/: Intended space for a future web-based interface.
- Final_Submission/: Place for final deliverables or exported reports.

## Workflow

1. Start with the chat parser notebook to convert the chat export into structured data.
2. Run the follow-up notebooks in order to generate overview metrics, activity insights, and participant analysis.
3. Use the final report notebook to combine the outputs into a single summary.

## Suggested usage

- Place a WhatsApp chat export in the dataset or data folder.
- Open the notebooks in the Development folder and run them sequentially.
- Review the generated pickle files in the Data folder for intermediate results.

## Notes

This project is currently notebook-driven and is a strong foundation for a future Streamlit or web-based dashboard experience.