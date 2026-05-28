resource "azurerm_storage_account" "adls" {
  name                          = "samain${var.resource_name_suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  account_kind                  = "StorageV2"
  is_hns_enabled                = true
  public_network_access_enabled = true

  network_rules {
    default_action             = "Allow"
    bypass                     = ["AzureServices"]
    virtual_network_subnet_ids = var.allowed_subnet_ids
  }
  tags = var.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "layers" {
  for_each           = toset(var.sa_container_names)
  name               = each.key
  storage_account_id = azurerm_storage_account.adls.id
}