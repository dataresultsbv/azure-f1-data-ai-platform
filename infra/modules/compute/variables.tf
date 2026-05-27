variable "resource_name_suffix" {
  type        = string
}

variable "location" {
  type        = string
}

variable "resource_group_name" {
  type        = string
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "infra_subnet_id" {
  type        = string
}

variable "image_name" {
  type        = string
  default     = "mcr.microsoft.com/azuredocs/aci-helloworld:latest" # Tijdelijke placeholder totdat je eigen image klaar is
}