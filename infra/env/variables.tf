variable "resource_name_suffix" {
  type        = string
  description = "The unique suffix for the project (eg. afdap)"
}

variable "location" {
  type        = string
  description = "The Azure region where the resource will be hosted"
  default     = "West Europe"
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "network" {
  type = map(object(
    {
      vnet_address_space = list(string)
      snets = map(object(
        {
          snet_address_prefix = list(string)
          delegation          = optional(string, null)
          service_endpoints   = optional(list(string), [])
        }
      ))
    }
  ))
}

variable "sa_container_names" {
  type = list(string)
}

variable "f1_api_ingestion_ci" {
  type = object(
    {
      ci_name           = string
      start_season      = string
      end_season        = string
      sa_container_name = string
    }
  )
}

variable "f1_transformation_ci" {
  type = object(
    {
      ci_name      = string
      start_season = string
      end_season   = string
    }
  )
}

variable "f1_aggregation_ci" {
  type = object(
    {
      ci_name      = string
      start_season = string
      end_season   = string
    }
  )
}