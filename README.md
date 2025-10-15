## AI Attendance Calculator — README

One-line: AI Attendance Calculator is a lightweight tool that estimates, predicts, and helps manage student attendance using computer-vision or log data and simple ML rules — with explanations, alerts, and a CLI/API for easy integration.

## Table of contents

Overview

Features

Quick start (install & run)

Usage examples (CLI & API)

Data formats & model behavior

Deployment (Docker)

Privacy & security

Troubleshooting

Contributing

## License & credits

Overview

AI Attendance Calculator (AAC) helps instructors and admins automatically compute attendance, predict at-risk students, and generate easy-to-read reports. The project supports two input modes:

Log mode — parse class logs (CSV / JSON) from LMS or card readers.

Vision mode — (optional) use a pre-trained face-recognition pipeline to mark presence from images/video frames.

The system combines deterministic rules (time windows, thresholds) with explainable ML (simple classifier/regression) to predict whether a student is likely to be present/absent or at risk of low attendance.

Designed to be modular, privacy-first, and easy to integrate into college portals or Discord/Slack bots.

## Features

✅ Parse attendance from CSV / JSON logs

✅ Optional face-based presence detection (plug-in module)

✅ Predictive risk scoring (who’s likely to dip below required % next exam)

✅ CLI, REST API, and batch job modes

✅ Configurable parameters (grace period, minimum % requirement)

✅ Human-readable explanations for predictions (why a student is flagged)

✅ CSV, PDF and JSON report exports

✅ Lightweight — runs locally or in a Docker container

## Quick start
Requirements

Python 3.10+

pip (or poetry)

Recommended: Docker (for containerized run