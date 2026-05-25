terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.53.0" 
    }
  }
}

provider "azurerm" {
  features {}
    subscription_id = "4b048a5c-a5de-4847-b059-b9124362adbf"
}