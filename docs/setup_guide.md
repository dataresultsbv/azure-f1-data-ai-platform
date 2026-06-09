# 🚀 Azure Data Platform - Setup & Deployment Guide

This document contains the complete step-by-step matrix for initializing, deploying, validating, and cleaning up version 1 of the end-to-end F1 Data Platform on Azure. The framework utilizes Terraform for Core Infrastructure and GitHub Actions for the Agentic CI/CD pipelines.

---

## 📋 Prerequisites

Before starting, ensure you are logged into Azure via your terminal and targeting the correct subscription:

```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
``` 

## 🛠️ Deployment Steps

### Step 1: Bootstrap the Azure Environment (Local)
The bootstrap script sets up the foundational resources that fall outside the regular Terraform lifecycle. This includes the storage account for remote state locking and the OIDC Identity/Federated Credentials for GitHub Actions.

Open your terminal and navigate to the root of the repository.

Make the script executable and run it:

```bash
chmod +x ./scripts/create_bootstrap.sh
./scripts/create_bootstrap.sh
```

### Step 2: Update GitHub Repository Secrets
The bootstrap script generates a output at the end containing the required OIDC credentials.

In GitHub, navigate to: Settings -> Secrets and variables -> Actions.

Add the following Repository Secrets (or overwrite the existing ones):

AZURE_CLIENT_ID

AZURE_TENANT_ID

AZURE_SUBSCRIPTION_ID

### Step 3: Deploy Core Infrastructure (GitHub Action)
Now that GitHub is trusted via Azure OIDC, the full infrastructure (Resource Group, ADLS Gen2 Medallion architecture, Azure Container Registry, and User-Assigned Managed Identities) can be deployed.

Go to the Actions tab in your GitHub repository.

Select the workflow: 1a. Core Infrastructure Deployment.

Click Run workflow -> Select the main branch -> Click Run workflow.

### Step 4: Activate F1 Ingestion CD (GitHub Action)
Once the base infrastructure is up, this pipeline builds the Docker image for the API ingestion, executes the live integration tests, pushes the image to the ACR, and spins up the ACI with the correct User-Assigned Identity attached.

In the Actions tab, select the workflow: 2b. F1 Ingestion CD.

Click Run workflow -> Select the main branch -> Click Run workflow.

### Step 5: Automatic Trigger - F1 Transformation CD 🔄
The transformation pipeline does not need to be started manually.

The workflow 3b. F1 Transformation CD utilizes a workflow_run trigger that listens specifically to the completion status of 2b. F1 Ingestion CD.

As soon as the Ingestion container successfully completes its run (and drops the raw data into the bronze Data Lake Gen2 container), the transformation pipeline automatically kicks off to process the data transition into silver.

### Step 6: Automatic Trigger - F1 Aggregation CD 🏗️
The aggregation pipeline runs completely hands-off once the data is cleaned.

The workflow 4b. F1 Aggregation CD triggers automatically on the completion of 3b. F1 Transformation CD.

This stage builds the aggregation engine, launches an Azure Container Instance using its assigned identity context, runs your analytical metrics calculations over the silver delta layer, and generates the final high-performance business views into the gold data lake container as Parquet.

### Step 7: Automatic Trigger - F1 Dashboard CD 📊
The presentation layer updates automatically once the data tier finishes processing.

The workflow 5. F1 Dashboard CD utilizes a workflow_run trigger that listens directly for the successful completion of 4b. F1 Aggregation CD.

As soon as the aggregation pipeline finishes generating the final metrics and saves the gold Parquet files into ADLS Gen2, the dashboard pipeline kicks off. It connects securely via Azure OIDC, pulls the fresh data directly from the gold storage container, ingests the sources, and compiles your Evidence site. Finally, it uses the Azure CLI to dynamically query the SWA deployment key into memory and ships the built assets directly to Azure Static Web Apps—keeping the entire CI/CD process completely secretless.

## 🧹 Teardown/Destroy
To avoid unnecessary cloud costs when not actively developing, the entire environment can be destroyed in reverse order.

### Step 1: Destroy Core Infrastructure (GitHub Action)
This removes all operational resources (Storage Accounts, Container Registries, and Container Groups) but leaves the remote state storage intact.

Go to the Actions tab in GitHub.

Select the workflow: 1b. Core Infrastructure Destroy.

Click Run workflow -> Select the main branch -> Click Run workflow.

### Step 2: Destroy Bootstrap Environment (Local)
Finally, remove the last remaining traces on the Azure side (the Resource Group containing the Terraform state and the App Registration/Identity).

Open your terminal and run the destroy script:

```bash
chmod +x ./scripts/destroy_bootstrap.sh
./scripts/destroy_bootstrap.sh
```