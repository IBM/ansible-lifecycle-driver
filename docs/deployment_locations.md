# Deployment Locations

A deployment location must be provided to a lifecycle request to indicate the Kubernetes environment to be used. The deployment location will be managed by Brent (Resource Manager) but must have particular properties to be successfully used by this driver.

# Properties

The following properties are supported by the driver:

| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| os_api_url      | -       | Y                                  | Defines the address of the Openstack environment. This address will be used for all API requests, including authentication |
| os_auth_enabled | True    | N                                  | Informs the driver that the Openstack environment requires authentication with keystone                                    |
| os_auth_api     | -       | Y - when `os_auth_enabled` is True | Defines the authentication API endpoint used to make authentication requests by this driver                                |

This driver currently supports password authentication only. The following properties may be set on a deployment location to configure the user for all requests:

| Name                        | Type    | Detail                          |
| --------------------------- | ------- | ------------------------------- |
| os_auth_domain_id           | String  | ID for domain scoping           |
| os_auth_domain_name         | String  | Name for domain scoping         |
| os_auth_project_id          | String  | ID for project scoping          |
| os_auth_project_name        | String  | Name for project scoping        |
| os_auth_project_domain_id   | String  | Domain ID for named project     |
| os_auth_project_domain_name | String  | Domain name for named project   |
| os_auth_trust_id            | String  | ID for trust scoping            |
| os_auth_user_id             | String  | ID of user for authentication   |
| os_auth_username            | String  | Name of user for authentication |
| os_auth_user_domain_id      | String  | Domain ID for named user        |
| os_auth_user_domain_name    | String  | Domain name for named user      |
| os_auth_password            | String  | Password for user               |
| os_auth_unscoped            | Boolean | Use unscoped tokens             |

You will not need to provide values for all of the above properties, it depends on the type of scoping you require. You must use one of the following combinations:

- domain_id
- domain_name
- project_id
- project_name + project_domain_id
- project_name + project_domain_name
- trust_id
- unscoped

In addition, you must set the user and password with one of the following combinations:

- user_id + user_domain_id + password
- user_id + user_domain_name + password
- username + password

The following example shows a full set of valid properties for an Openstack deployment location:

```
"properties": {
    "os_auth_project_name": "my-project",
    "os_auth_project_domain_name": "default",
    "os_auth_password": "secret",
    "os_auth_username": "my-user",
    "os_auth_user_domain_name": "default",
    "os_auth_api": "identity/v3",
    "os_api_url": "http://10.10.8.8"
}
```
