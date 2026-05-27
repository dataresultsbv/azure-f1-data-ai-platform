variable "resource_name_suffix" {
  type        = string
  description = "The unique suffix for the project (eg. afdap)"
}

variable "resource_group_name" {
  type        = string
  description = "The name of the Resource Group"
}

variable "location" {
  type        = string
  description = "The Azure region"
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "allowed_subnet_ids" {
  type        = list(string)
  description = "List of Subnet IDs that will have access to this Storage Account"
  default     = []
}

variable "allowed_ip_ranges" {
  type        = list(string)
  description = "List of public IP addresses or CIDR notations (e.g., ['82.95.x.x']) that will have temporary access to the Storage Account"
  default     = []
}