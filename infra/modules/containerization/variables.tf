variable "resource_name_suffix" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "storage_account_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
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