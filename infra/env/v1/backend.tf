terraform {
  backend "azurerm" {
    resource_group_name  = "rg-afdap-tfstate"
    storage_account_name = "satfstateafdap123987123"
    container_name       = "tfstates"
    key                  = "v1/terraform.tfstate"
    use_oidc             = true
  }
}
