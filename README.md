# Titanic API Project

## Project Description
This API project implements the requested five HTTP endpoints based on Swagger, and all of them are returning the requested request and response bodies.
There is a docker-compose folder that includes a docker-compose.yaml file, and MariaDB login details that you can use to automatically build the image, and run the application locally.

The Database is automatically created from MariaDB, the table and all records are automatically created from the "\_\_main_\_" python script located in swagger_server/\_\_main_\_.py location by using the **Pandas** library.

The API container is running under the user : "**python**", while MariaDB container is running under the user "**mysql**".

The API logic, is coded in swagger_server/controllers/default_controller.py by using the **mysql-connector-python** library to establish a database connection, and perform all CRUD operations. Related queries were manually crafted. **Response Codes** and **Response Messages** are returned according to Swagger Specification.

The **k8s** folder includes all nessesary .yaml files for the application to run. **GKE** is used for the deployments, and database persistence is achived with automatic volume provisioning via the standard-rwo GKE storage class.

This project, except from the API and MariaDB is also installing:
1. **Haproxy Ingress Controller**.
2. **CertManager**.
3. **External-DNS** (Option given not to install).
4. **NetData Monitoring-Observability Tool**. (You will be asked to enter your NETDATA_TOKEN and NETDATA_ROOMS).
The Token and Room variables can be obtained from [NetData Cloud](https://app.netdata.cloud/) by clicking "Connect Nodes" on the left pane, and then by clicking on the "Kubernetes" button on the right pane.

## Programming Languages Used
1. **Bash**
2. **Python**
## Installation
By initiating the installation script you will be asked to enter:
1. **Your Image Tag** (will be automatically pushed to DockerHub).
2. **The Domain Name** where the API will be available.

If you don't have domain entries set up in Cloud DNS, you can choose to have them automatically set up by selecting 'y' when asked to install **External-DNS**. 

**Service Account**, **DNS Role**, **Secret** and **IAM-POLICY-BINDING** will be automatically created. 

To deploy the application to GKE you will only have to run the command below:
```
sudo chmod a+x install.sh && source install.sh
```
## Demo
You can test the API deployed on GKE at  [https://kubedemo.xyz/ui](https://kubedemo.xyz/ui/).