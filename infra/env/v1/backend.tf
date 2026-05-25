terraform {
  backend "azurerm" {
    resource_group_name  = "rg-afdap-tfstate"
    storage_account_name = "saafdap123987123"
    container_name       = "tfstates"
    key                  = "v1/terraform.tfstate"
  }
}
