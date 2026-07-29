---
name: report-summarizer
description: Summarize a business report into up to three factual highlights and one bottom-line sentence. Use when a user pastes report text and asks for a quick summary.
allowed-tools: [Read]
---
# Report Summarizer

Turn raw report text into a short, skimmable summary.

## Steps

1. Read the report text the user provides.
2. Extract up to three factual highlights (numbers, trends, incidents) as short bullet points.
3. Write one "Bottom line" sentence that states the overall takeaway in plain language.
4. Return only the bullets and the bottom-line sentence, nothing else.
