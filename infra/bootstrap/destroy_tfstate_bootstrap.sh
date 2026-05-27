#!/usr/bin/env bash

# -e: Exit on error
# -u: Error on undefined variables
# -o: Return exit status of first cmd that fails 
set -euo pipefail

# --- CONFIGS --- #
RESOURCE_GROUP_NAME="rg-afdap-tfstate"

echo "======================================="
echo "Starting Enterprise TFState Destroy"
echo "======================================="

echo "STATUS - Checking Azure CLI connection..."
if ! az account show &>/dev/null; then
    echo "ERROR - You are not logged in to Azure CLI. Start 'az login' first."
    exit 1
fi
echo "SUCCES - Azure CLI connection is active."

###########################################
########## DESTROY RESOURCE GROUP #########
###########################################

RG_EXISTS=$(az group exists --name "$RESOURCE_GROUP_NAME" --output tsv)

if [ "$RG_EXISTS" == "true" ]; then
    echo "STATUS - Deleting Resource Group '$RESOURCE_GROUP_NAME' and all its resources..."
    az group delete --name "$RESOURCE_GROUP_NAME" --yes
    echo "SUCCES - '$RESOURCE_GROUP_NAME' deleted"
else
    echo "INFO - Resource Group '$RESOURCE_GROUP_NAME' does not exist. Nothing to delete."
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
echo "Successfully finished Destroy TFState script"
echo "================================================================"