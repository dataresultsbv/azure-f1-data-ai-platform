#  Cruciale details voor je GitHub Workflow
#  Wanneer je dit script dadelijk in een GitHub Actions-omgeving gaat draaien, zijn er twee zaken waar je op moet letten:
#  
#  Maak het script uitvoerbaar:
#  Linux (en dus ook de GitHub runner) accepteert het script pas als het de juiste rechten heeft. Draai dit commando eenmalig in je terminal en commit de wijziging:
#  
#  Bash
#  chmod +x infra/bootstrap/destroy.sh
#  De always() vlag in GitHub Actions:
#  Als een integratietest halverwege je workflow faalt, stopt GitHub normaal gesproken direct met de opvolgende stappen. Je wilt echter dat de opruimactie altijd draait, ook bij een crash. In je GitHub YAML-bestand richt je dat straks zo in:
#  
#  YAML
#  - name: Cleanup Azure Bootstrap Environment
#    if: always() # <-- Dit zorgt ervoor dat de destroy ALTIJD wordt uitgevoerd
#    run: ./infra/bootstrap/destroy.sh



#!/usr/bin/env bash

# -e: Exit on error
# -u: Error on undefined variables
# -o: Return exit status of first cmd that fails 
set -euo pipefail

# --- CONFIGS --- #
RESOURCE_GROUP_NAME="rg-afdap-tfstate"

echo "======================================="
echo "Starting Enterprise Terraform Destroy"
echo "======================================="

echo "STATUS - Checking Azure CLI connection..."
if ! az account show &>/dev/null; then
    echo "ERROR - You are not logged in to Azure CLI. Start 'az login' first."
    exit 1
fi
echo "SUCCES - Azure CLI connection is active."

RG_EXISTS=$(az group exists --name "$RESOURCE_GROUP_NAME" --output tsv)

if [ "$RG_EXISTS" == "true" ]; then
    echo "STATUS - Deleting Resource Group '$RESOURCE_GROUP_NAME' and all its resources..."
    az group delete --name "$RESOURCE_GROUP_NAME" --yes
    echo "SUCCES - '$RESOURCE_GROUP_NAME' deleted"
else
    echo "INFO - Resource Group '$RESOURCE_GROUP_NAME' does not exist. Nothing to delete."
fi

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ENV_DIR="${INFRA_DIR}/env/v1"
BACKEND_OUTPUT_PATH="${TARGET_ENV_DIR}/backend.tf"

echo "STATUS - Cleaning up local backend.tf configuration..."
if [ -f "$BACKEND_OUTPUT_PATH" ]; then
    rm "$BACKEND_OUTPUT_PATH"
    echo "SUCCES - Removed local backend.tf file."
else
    echo "INFO - No local backend.tf file found to remove."
fi

echo "================================================================"
echo "Successfully finished Destroy.sh script"
echo "================================================================"