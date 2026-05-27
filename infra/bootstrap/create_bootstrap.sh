#!/usr/bin/env bash
set -euo pipefail

# --- CONFIGS --- #
LOCATION="West Europe"

# Identity Configs
MI_RESOURCE_GROUP="rg-afdap-mi"
MI_NAME="rg-afdap-mi-12398723"

# TFState Configs
TFSTATE_RESOURCE_GROUP="rg-afdap-tfstate"
STORAGE_ACCOUNT_NAME="satfstateafdap123987123"
CONTAINER_NAME="tfstates"

# GITHUB CONFIGS
GH_ORGANIZATION="dataresultsbv"
GH_REPOSITORY="azure-f1-data-ai-platform"

echo "========================================================"
echo "Starting Full Enterprise Infrastructure Bootstrap (OIDC)"
echo "========================================================"

echo "STATUS - Checking Azure CLI connection..."
if ! az account show &>/dev/null; then
    echo "ERROR - You are not logged in to Azure CLI. Start 'az login' first."
    exit 1
fi
echo "SUCCES - Azure CLI connection is active."

########################################################
# PART 1: MANAGED IDENTITY & OIDC LAYER               #
########################################################
echo "STATUS - Progressing with Part 1: Identity Layer..."

# Create Identity Resource Group
RG_MI_EXISTS=$(az group exists --name "$MI_RESOURCE_GROUP" --output tsv)
if [ "$RG_MI_EXISTS" == "false" ]; then
    echo "STATUS - Creating Resource Group '$MI_RESOURCE_GROUP'..."
    az group create --name "$MI_RESOURCE_GROUP" --location "$LOCATION" -o table
    echo "SUCCES - Succesfully created '$MI_RESOURCE_GROUP'"
else
    echo "INFO - Resource Group '$MI_RESOURCE_GROUP' already exists."
fi

# Create Managed Identity
MI_EXISTS=$(az identity list --resource-group "$MI_RESOURCE_GROUP" --query "[?name=='$MI_NAME']" | jq 'if length > 0 then "true" else "false" end' -r)
if [ "$MI_EXISTS" == "false" ]; then
    echo "STATUS - Creating Managed Identity '$MI_NAME'..."
    az identity create --name "$MI_NAME" --resource-group "$MI_RESOURCE_GROUP" --location "$LOCATION" -o table
    echo "SUCCES - Succesfully created '$MI_NAME'"
else
    echo "INFO - Managed Identity '$MI_NAME' already exists."
fi

# Vars for github secrets
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
MI_PRINCIPAL_ID=$(az identity show --name "$MI_NAME" --resource-group "$MI_RESOURCE_GROUP" --query "principalId" -o tsv)
MI_CLIENT_ID=$(az identity show --name "$MI_NAME" --resource-group "$MI_RESOURCE_GROUP" --query "clientId" -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Assign Contributor to Subscription
echo "STATUS - Assigning Contributor role on Subscription level to Identity..."

MAX_RETRIES=6
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if az role assignment create \
        --assignee "$MI_PRINCIPAL_ID" \
        --role "Contributor" \
        --scope "/subscriptions/$SUBSCRIPTION_ID" \
        --output none 2>/dev/null; then
        echo "SUCCES - Role assignment created successfully."
        SUCCESS=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "INFO - Entra ID replication delay detected. Retrying role assignment in 10 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 10
    fi
done

if [ "$SUCCESS" = false ]; then
    echo "ERROR - Failed to assign Contributor role after $MAX_RETRIES attempts due to Azure replication issues."
    exit 1
fi

# Create Federated Credentials
declare -A CREDENTIALS=(
    ["fed-cred-main"]="repo:${GH_ORGANIZATION}/${GH_REPOSITORY}:ref:refs/heads/main"
    ["fed-cred-env-prod"]="repo:${GH_ORGANIZATION}/${GH_REPOSITORY}:environment:production"
    ["fed-cred-dispatch"]="repo:${GH_ORGANIZATION}/${GH_REPOSITORY}:event:workflow_dispatch"
)

for CRED_NAME in "${!CREDENTIALS[@]}"; do
    SUBJECT="${CREDENTIALS[$CRED_NAME]}"
    CRED_EXISTS=$(az identity federated-credential list --identity-name "$MI_NAME" --resource-group "$MI_RESOURCE_GROUP" --query "[?name=='$CRED_NAME'].id" -o tsv)
    
    if [ -z "$CRED_EXISTS" ]; then
        echo "STATUS - Creating Federated Credential '$CRED_NAME'..."
        az identity federated-credential create \
            --name "$CRED_NAME" \
            --identity-name "$MI_NAME" \
            --resource-group "$MI_RESOURCE_GROUP" \
            --issuer "https://token.actions.githubusercontent.com" \
            --subject "$SUBJECT" \
            --audience "api://AzureADTokenExchange" \
            --output none
    else
        echo "INFO - Federated Credential '$CRED_NAME' already exists."
    fi
done

########################################################
# PART 2: TFSTATE STORAGE LAYER                        #
########################################################
echo "STATUS - Progressing with Part 2: Storage Layer..."

# Create TFState Resource Group
RG_STATE_EXISTS=$(az group exists --name "$TFSTATE_RESOURCE_GROUP" --output tsv)
if [ "$RG_STATE_EXISTS" == "false" ]; then
    echo "STATUS - Creating Resource Group '$TFSTATE_RESOURCE_GROUP'..."
    az group create --name "$TFSTATE_RESOURCE_GROUP" --location "$LOCATION" -o table
    echo "SUCCES - Succesfully created '$TFSTATE_RESOURCE_GROUP'"
else
    echo "INFO - Resource Group '$TFSTATE_RESOURCE_GROUP' already exists."
fi

# Create Storage Account
SA_NAME_AVAILABLE=$(az storage account check-name --name "$STORAGE_ACCOUNT_NAME" --query "nameAvailable" -o tsv)
if [ "$SA_NAME_AVAILABLE" == "true" ]; then
    echo "STATUS - Creating Storage Account '$STORAGE_ACCOUNT_NAME'..."
    az storage account create \
      --name "$STORAGE_ACCOUNT_NAME" \
      --resource-group "$TFSTATE_RESOURCE_GROUP" \
      --location "$LOCATION" \
      --sku Standard_LRS \
      --kind StorageV2 \
      --allow-blob-public-access false \
      --min-tls-version TLS1_2 \
      --default-action Allow \
      -o table
    echo "SUCCES - Created '$STORAGE_ACCOUNT_NAME'"
else
    echo "INFO - Storage Account '$STORAGE_ACCOUNT_NAME' already exists."
    echo "STATUS - Ensuring public network access is allowed for CI/CD runners..."
    az storage account update \
      --name "$STORAGE_ACCOUNT_NAME" \
      --resource-group "$TFSTATE_RESOURCE_GROUP" \
      --default-action Allow \
      --bypass AzureServices \
      --output none
fi

# Create Container
CONTAINER_EXISTS=$(az storage container exists --name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT_NAME" --auth-mode login --query "exists" -o tsv)
if [ "$CONTAINER_EXISTS" == "false" ]; then
    echo "Creating Blob Container '$CONTAINER_NAME'..."
    az storage container create \
      --name "$CONTAINER_NAME" \
      --account-name "$STORAGE_ACCOUNT_NAME" \
      --auth-mode login \
      --output none
    echo "SUCCES - Created '$CONTAINER_NAME'"
else
    echo "INFO - Blob Container '$CONTAINER_NAME' already exists."
fi  

# Assign Blob Data Contributor to Managed Identity
echo "STATUS - Assigning Storage Blob Data Contributor role to Managed Identity..."
az role assignment create \
  --assignee "$MI_PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$TFSTATE_RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME" \
  --output none
echo "SUCCES - Managed Identity now has Data Contributor access to TFState Storage."

########################################################
# PART 3: GENERATE BACKEND CONFIGURATIONS              #
########################################################
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for ENV in "v1" "v2"; do
    echo "STATUS - Generating backend.tf config for $ENV..."
    TARGET_ENV_DIR="${INFRA_DIR}/env/${ENV}"
    BACKEND_OUTPUT_PATH="${TARGET_ENV_DIR}/backend.tf"

    mkdir -p "$TARGET_ENV_DIR"

    cat << EOF > "$BACKEND_OUTPUT_PATH"
terraform {
  backend "azurerm" {
    resource_group_name  = "$TFSTATE_RESOURCE_GROUP"
    storage_account_name = "$STORAGE_ACCOUNT_NAME"
    container_name       = "$CONTAINER_NAME"
    key                  = "${ENV}/terraform.tfstate"
    use_oidc             = true
  }
}
EOF
    echo "SUCCES - Wrote backend.tf to $BACKEND_OUTPUT_PATH"
done

########################################################
# PART 4: OUTPUT INSTRUCTIONS                         #
########################################################

clear
echo "================================================================"
echo "SUCCES - Identity Layer is ready!"
echo "Put these secrets in your GitHub Repository as Repository Secrets:"
echo "AZURE_CLIENT_ID:       $MI_CLIENT_ID"
echo "AZURE_TENANT_ID:       $(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo "================================================================"