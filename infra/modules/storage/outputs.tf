output "storage_account_id" {
  value       = azurerm_storage_account.adls.id
  description = "The ID of the created Storage Account"
}

output "primary_dfs_endpoint" {
  value       = azurerm_storage_account.adls.primary_dfs_endpoint
  description = "The DFS endpoint for ADLS Gen2 connections"
}