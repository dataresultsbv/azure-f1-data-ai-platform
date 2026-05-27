#!/usr/bin/env bash
set -euo pipefail

# --- CONFIGS --- #
MI_RESOURCE_GROUP="rg-afdap-mi"
TFSTATE_RESOURCE_GROUP="rg-afdap-tfstate"

echo "========================================================"
echo "Starting Full Enterprise Infrastructure Destroy (OIDC)"
echo "========================================================"

echo "STATUS - Checking Azure CLI connection..."
if ! az account show &>/dev/null; then
    echo "ERROR - You are not logged in to Azure CLI. Start 'az login' first."
    exit 1
fi
echo "SUCCES - Azure CLI connection is active."

###########################################
########## DESTROY RESOURCE GROUPS ########
###########################################

# Destroy TFState Storage Group
RG_STATE_EXISTS=$(az group exists --name "$TFSTATE_RESOURCE_GROUP" --output tsv)
if [ "$RG_STATE_EXISTS" == "true" ]; then
    echo "STATUS - Deleting Resource Group '$TFSTATE_RESOURCE_GROUP' and all state data..."
    az group delete --name "$TFSTATE_RESOURCE_GROUP" --yes
    echo "SUCCES - '$TFSTATE_RESOURCE_GROUP' deleted"
else
    echo "INFO - Resource Group '$TFSTATE_RESOURCE_GROUP' does not exist."
fi

# Destroy Managed Identity Group
RG_MI_EXISTS=$(az group exists --name "$MI_RESOURCE_GROUP" --output tsv)
if [ "$RG_MI_EXISTS" == "true" ]; then
    echo "STATUS - Deleting Resource Group '$MI_RESOURCE_GROUP' and all identities..."
    az group delete --name "$MI_RESOURCE_GROUP" --yes
    echo "SUCCES - '$MI_RESOURCE_GROUP' deleted"
else
    echo "INFO - Resource Group '$MI_RESOURCE_GROUP' does not exist."
fi

###########################################
########## CLEANUP BACKEND FILES ##########
###########################################

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for ENV in "v1" "v2"; do
    TARGET_ENV_DIR="${INFRA_DIR}/env/${ENV}"
    BACKEND_OUTPUT_PATH="${TARGET_ENV_DIR}/backend.tf"

    echo "STATUS - Cleaning up local backend.tf configuration for $ENV..."
    if [ -f "$BACKEND_OUTPUT_PATH" ]; then
        rm "$BACKEND_OUTPUT_PATH"
        echo "SUCCES - Removed local backend.tf file for $ENV."
    else
        echo "INFO - No local backend.tf file found to remove for $ENV."
    fi
done

echo "================================================================"
echo "Successfully finished complete Destroy script"
echo "================================================================"