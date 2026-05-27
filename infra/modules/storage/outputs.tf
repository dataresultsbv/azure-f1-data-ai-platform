output "storage_account_id" {
  value       = azurerm_storage_account.adls.id
  description = "The ID of the created Storage Account"
}

output "storage_account_name" {
  value       = azurerm_storage_account.adls.name
  description = "The name for the storage account"
}