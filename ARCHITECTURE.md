# OCML-DI System Architecture

## Overview
OCML-DI is an offline-first healthcare safety platform designed for African infrastructure realities. It enables portable patient records, drug interaction intelligence, and USSD access for feature phones.

## Core Components
- **Patient QR Wallet**: Encrypted portable medical record.
- **Clinician Dashboard**: Web interface for patient management and risk checks.
- **USSD Router**: Feature phone access for drug safety checks.
- **Risk Engine**: Evaluates drug-to-drug, drug-to-condition, and drug-to-allergy risks.
- **Governance Layer**: Human-in-the-loop review for critical alerts.
- **Audit Logging**: Records all actions for transparency and accountability.
- **Local Database**: SQLite persistence with offline-first design.
- **Optional Cloud Sync**: Synchronization when internet is available.

## Data Flow
Patient → QR Wallet → Clinician Dashboard/USSD → Risk Engine → Risk Scoring → Governance → Audit Logs

## Offline Resilience
- Core functionality requires no internet.
- Cloud sync is optional, not mandatory.
