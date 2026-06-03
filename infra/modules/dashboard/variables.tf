variable "resource_name_suffix" {
  type        = string
  description = "Suffix applied to all created infrastructure resources."
}

variable "location" {
  type        = string
  description = "Azure region where resources will be deployed."
}

variable "resource_group_name" {
  type        = string
  description = "Name of the target resource group."
}

variable "tags" {
  type        = map(string)
  default     = {}
}