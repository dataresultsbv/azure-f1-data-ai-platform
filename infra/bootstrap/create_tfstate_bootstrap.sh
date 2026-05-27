#!/usr/bin/env bash

# -e: Exit on error
# -u: Error on undefined variables
# -o: Return exit status of first cmd that fails 
set -euo pipefail

# --- CONFIGS --- #
RESOURCE_GROUP_NAME="rg-afdap-tfstate"
LOCATION="West Europe"
STORAGE_ACCOUNT_NAME="satfstateafdap123987123"
CONTAINER_NAME="tfstates"
MI_RESOURCE_GROUP="rg-afdap-mi"
MI_NAME="rg-afdap-mi-12398723"

echo "======================================="
echo "Starting Enterprise Terraform Bootstrap"
echo "======================================="

echo "STATUS - Checking Azure CLI connection..."
if ! az account show &>/dev/null; then
    echo "ERROR - You are not logged in to Azure CLI. Start 'az login' first."
    exit 1
fi
echo "SUCCES - Azure CLI connection is active."

###########################################
########## CREATE RESOURCE GROUP ##########
###########################################

RG_EXISTS=$(az group exists --name "$RESOURCE_GROUP_NAME" --output tsv)

if [ "$RG_EXISTS" == "false" ]; then
    echo "STATUS - Creating Resource Group '$RESOURCE_GROUP_NAME'..."
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION" -o table
    echo "SUCCES - Succesfully created '$RESOURCE_GROUP_NAME'"
else
    echo "INFO - Resource Group '$RESOURCE_GROUP_NAME' already exists."
fi

############################################
########## CREATE STORAGE ACCOUNT ##########
############################################

SA_NAME_AVAILABLE=$(az storage account check-name --name "$STORAGE_ACCOUNT_NAME" --query "nameAvailable" -o tsv)

if [ "$SA_NAME_AVAILABLE" == "true" ]; then
    echo "STATUS - Creating Storage Account '$STORAGE_ACCOUNT_NAME'..."
    az storage account create \
      --name "$STORAGE_ACCOUNT_NAME" \
      --resource-group "$RESOURCE_GROUP_NAME" \
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
fi

##########################################
############ CREATE CONTAINER ############
##########################################

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

###########################################
######### STORAGE NETWORK SECURITY #########
###########################################

echo "STATUS - Configuring Enterprise Network Security for TFState Storage..."

echo "STATUS - Configuring Network Rules for TFState Storage..."
az storage account update \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP_NAME" \
  --default-action Allow \
  --bypass AzureServices \
  --output none
echo "SUCCES - Network access is set to Allow. Authentication is fully governed by OIDC Identity tokens."

###########################################
####### ASSIGN IAM ROLES TO MI ############
###########################################

echo "STATUS - Fetching Managed Identity Principal ID..."
MI_PRINCIPAL_ID=$(az identity show \
  --name "$MI_NAME" \
  --resource-group "$MI_RESOURCE_GROUP" \
  --query "principalId" \
  --output tsv)

echo "STATUS - Assigning Storage Blob Data Contributor role to Managed Identity..."
az role assignment create \
  --assignee "$MI_PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME" \
  --output none

echo "SUCCES - Managed Identity now has Data Contributor access to TFState Storage."

###########################################
############ CREATE BACKEND.TF ############
###########################################

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for ENV in "v1" "v2"; do
  echo "STATUS - Generating backend.tf config for $ENV..."
  TARGET_ENV_DIR="${INFRA_DIR}/env/${ENV}"
  BACKEND_OUTPUT_PATH="${TARGET_ENV_DIR}/backend.tf"

  mkdir -p "$TARGET_ENV_DIR"

  cat << EOF > "$BACKEND_OUTPUT_PATH"
terraform {
  backend "azurerm" {
    resource_group_name  = "$RESOURCE_GROUP_NAME"
    storage_account_name = "$STORAGE_ACCOUNT_NAME"
    container_name       = "$CONTAINER_NAME"
    key                  = "${ENV}/terraform.tfstate"
    use_oidc             = true
  }
}
EOF
  echo "SUCCES - Wrote backend.tf to $BACKEND_OUTPUT_PATH"
done

echo "================================================================"
echo "Succesfully finished bootstrap.sh script"
echo "================================================================"