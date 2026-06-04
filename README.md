# Azure F1 Data & AI Platform

## Overview

This project is a cloud-native data and AI engineering platform built on Azure that explores how weather conditions influence Formula 1 races.

The platform combines historical Formula 1 race data with weather enrichment based on circuit geolocation, altitude, and race timestamps. By integrating race telemetry-related datasets with historical weather observations, the project evolves into a scalable analytics and agentic AI platform. The project starts with a strong data platform foundation and incrementally expands into API serving, AI-powered analytics, event-driven architectures, and MLOps capabilities.

Each version represents a maturity step in building a production-inspired Azure-native platform.

---

## Background

With over 15 years of experience in BI and data platforms, I have worked across the evolution from on-premise systems to modern cloud architectures on Azure.

Currently, a new shift is emerging. The shift from data platforms that process information to systems that can reason, decide, and act. This project captures that transition. 

The first version starts with a solid data platform foundation, onboarding F1 data from Jolpica F1 API. In the following version the data will be enriched with data from Open-Meteo Historical Weather API. 

Then cloud-native pipelines, and infrastructure-as-code evolves into an agentic AI platform with autonomous decision-making capabilities. 

The focus is not just on building components, but on designing systems that scale from data processing to intelligent, agent-driven architectures. This aligns with the next generation of Azure solutions and the path towards Agentic AI architecture.

---

## Core Use Case

The primary use case is to analyze how environmental conditions affect Formula 1 races.

By combining:

- Race schedules
- Circuit metadata
- Latitude / Longitude / Altitude
- Historical weather conditions
- Race outcomes
- Driver performance
- Incident history
- Strategy patterns

The platform can explore questions such as:

- How does rain affect race performance?
- Which circuits are most weather-sensitive?
- Which drivers outperform in wet conditions?
- Can weather conditions increase safety car probability?
- Can historical environmental patterns predict race risks?

---

## Repository Structure

The repository follows a modular structure where infrastructure, services, workflows, and documentation are organized by domain and version maturity.

```bash
azure-f1-data-ai-platform/
│
├── .github/
├── docs/
├── f1-dashboard/
├── infra/
├── src/
```

### `.github/`
Contains GitHub Actions workflows for:

- CI/CD pipelines
- Terraform validation and deployment
- Docker image builds
- Release workflows

### `docs/`
Contains project version specific documentation, including:

- Architecture diagrams
- Design considerations
- Setup Guide

### `f1-dashboard/`
Contains setup files and configuration for a static webpage dashboard using Evidence.

- Page definition
- Source SQL query definition.

### `infra/`
Contains Infrastructure-as-Code built with Terraform.

Structure is based on reusable modules and environment/version-specific deployments.

Examples:

- Storage
- Azure Container Registry
- Key Vault
- Container Apps
- AI services
- MLOps-related infrastructure

### `src/`
Contains all Python-based platform services and domain logic.

This includes:

- F1 data ingestion
- Weather data ingestion
- Transformations
- Feature engineering
- API services
- AI workflows
- ML pipelines