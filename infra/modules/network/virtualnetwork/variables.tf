variable "resource_name_suffix" {
  type        = string
  description = "The unique suffix for the project (eg. afdap)"
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group"
}

variable "location" {
  type        = string
  description = "The Azure region where the resource will be hosted"
  default     = "West Europe"
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "vnet_details" {
  type = list(object(
    {
      vnet_name = string
      vnet_address_space = list(string)
    }
  ))
}

variable "snet_details" {
  type = list(object(
    {
      snet_name = string
      vnet_name = string
      snet_address_prefix = list(string)
      snet_delegation = string
    }
  ))
}