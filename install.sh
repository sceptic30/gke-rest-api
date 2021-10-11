#!bin/bash
export CYAN="\e[96m"
export YELLOW="\e[33m"
export GREEN="\e[32m"

add_image_tag='y'
while [[ "$add_image_tag" == y ]]; do
    read -p 'Add DOMAIN NAME: ' BASE_DOMAIN
    read -p 'Add Image Tag To Be Built: ' IMAGE_TAG
    add_image_tag='n'
done
echo -e "${CYAN}Your Image Tag is: ${ENDCOLOR}" ${IMAGE_TAG}
docker build . -t $IMAGE_TAG

echo -e "${CYAN}Adjusting Manifests To Given Image Tag${ENDCOLOR}"

replacement="$IMAGE_TAG"
sed -i "s@api_image@$replacement@" k8s/api.yaml
sed -i "s@api_image@$replacement@" docker-compose/docker-compose.yaml

echo -e "${CYAN}Pushing Image To DockerHub For Kubernetes To Download It${ENDCOLOR}"
docker push $IMAGE_TAG

#######----------------------------------------------------------------------#########

echo -e "${YELLOW}Creating NameSpace For The Deployment${ENDCOLOR}"
kubectl create ns titanic-api

echo -e "${YELLOW}Creating Secret For MySQL Database${ENDCOLOR}"
kubectl create secret generic mysql-secret --from-literal=MYSQL_ROOT_PASSWORD='Fp~i*34aB{v*' --from-literal=MYSQL_DATABASE=titanicDB --from-literal=MYSQL_USER=nikos --from-literal=MYSQL_PASSWORD=nikos1575 -n titanic-api

echo -e "${YELLOW}Deploying MySQL Database${ENDCOLOR}"
kubectl apply -f k8s/mysql.yaml
sleep 5
echo -e "${YELLOW}Waiting For MySQL Pod To Become Available...${ENDCOLOR}"
kubectl wait --for=condition=Ready pod/db-0 -n titanic-api --timeout=60s

#######----------------------------------------------------------------------#########
echo "Deploying API.."
kubectl apply -f k8s/api.yaml
sleep 5
echo -e "${YELLOW}Waiting For API POD To Become Available...${ENDCOLOR}"
kubectl wait --for=condition=Ready pod/api-0 -n titanic-api --timeout=60s

#######----------------------------------------------------------------------#########
echo -e "${YELLOW}Deploying Haproxy Ingress Controller.${ENDCOLOR}"
kubectl create ns haproxy-ingress
kubectl apply -f k8s/haproxy/ingress-install.yaml

#######----------------------------------------------------------------------#########
read -p 'Would You Like To Install External-DNS For DNS Entries AutoConfiguration? (y/n): ' add_external_dns

if [[ "$add_external_dns" == y ]]; then
    echo -e "${YELLOW}Deploying External-DNS...${ENDCOLOR}"
    kubectl create ns external-dns

    add_project_id='y'
    while [[ "$add_project_id" == y ]]; do
        read -p 'Add PROJECT ID: ' PROJECT_ID
        add_project_id='n'
    done

    echo -e "${GREEN}Applying given BASE_DOMAIN to related files${ENDCOLOR}"
    sed -i "s/--domain-filter=example.com/--domain-filter=$BASE_DOMAIN/g" k8s/external-dns/install.yaml
    sed -i "s/--google-project=my_google_project/--google-project=$PROJECT_ID/g" k8s/external-dns/install.yaml
    
    gcloud config set project $PROJECT_ID
    dns_admin_sa=$(gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.members)" --filter="bindings.role:dns.admin" | grep external-dns)
    dns_admin_secr_exist=$(kubectl get secret external-dns-secret -n external-dns)
    sleep 3;
    if [ $dns_admin_sa ] && [ ! $dns_admin_secr_exist ];
        then 
            echo -e "${YELLOW}A service account with DNS.ADMIN Role already Exists. Skipping Creation Of Service Account and Creating Bind-Policy, Credentials and Secret ${ENDCOLOR}"
            gcloud projects add-iam-policy-binding $PROJECT_ID --role="roles/dns.admin" --member="serviceAccount:external-dns@$PROJECT_ID.iam.gserviceaccount.com"
            sleep 5;
            gcloud iam service-accounts keys create external-dns-credentials.json --iam-account external-dns@$PROJECT_ID.iam.gserviceaccount.com
            sleep 5;
            kubectl create secret generic external-dns-secret --from-file=credentials.json=external-dns-credentials.json -n external-dns        
        else 
            echo -e "${GREEN}Creating Service Account, Bind-Policy, Credentials and Secret${ENDCOLOR}"
            gcloud iam service-accounts create external-dns --display-name "Service account for ExternalDNS on GCP"
            sleep 5;
            gcloud projects add-iam-policy-binding $PROJECT_ID --role="roles/dns.admin" --member="serviceAccount:external-dns@$PROJECT_ID.iam.gserviceaccount.com"
            sleep 5;
            gcloud iam service-accounts keys create external-dns-credentials.json --iam-account external-dns@$PROJECT_ID.iam.gserviceaccount.com
            sleep 5;
            kubectl create secret generic external-dns-secret --from-file=credentials.json=external-dns-credentials.json -n external-dns
    fi
fi
sleep 2;
kubectl apply -f k8s/external-dns/install.yaml

#######----------------------------------------------------------------------#########
read -p 'Would You Like To Install CertManager To Auto Issue SSL Certificates? (y/n): ' add_cert_manager
if [[ "$add_cert_manager" == y ]]; then 
  read -p 'Enter An Email Address (For Cert Notifications): ' CLUSTER_ADMIN_EMAIL

  echo -e "${GREEN}Applying Provided Email Address To Cluster Issuers${ENDCOLOR}"
  sed -i "s/user@example.com/$CLUSTER_ADMIN_EMAIL/g" k8s/certmanager/production-issuer.yaml
  sed -i "s/user@example.com/$CLUSTER_ADMIN_EMAIL/g" k8s/certmanager/staging-issuer.yaml

  echo -e "${GREEN}Installing CertManager and configuring ClusterIssuers${ENDCOLOR}"
  kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.4.0/cert-manager.yaml
  sleep 30;
  kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.4.0/cert-manager.crds.yaml

  kubectl apply -f k8s/certmanager/production-issuer.yaml
  kubectl apply -f k8s/certmanager/staging-issuer.yaml
fi

echo -e "${YELLOW}Deploying Ingress Rules.${ENDCOLOR}"
sed -i "s/example.com/$BASE_DOMAIN/g" k8s/api-ingress.yaml
kubectl apply -f k8s/api-ingress.yaml

#######----------------------------------------------------------------------#########
echo -e "${GREEN}Installing NetData Observability-Monitoring Software${ENDCOLOR}"
read -p 'Enter Your NETDATA TOKEN: ' NETDATA_TOKEN
read -p 'Enter Your NETDATA ROOMS: ' NETDATA_ROOMS
kubectl create ns netdata
ACCESSMODE=ReadWriteOnce
STORAGE_CLASS=standard-rwo
git clone https://github.com/sceptic30/netdata-helmchart.git
sleep 1
sed -i "s/example.com/$BASE_DOMAIN/g" netdata-helmchart/charts/netdata/values.yaml
sleep 1
sed -i "s/token: \"\"/token: \"$NETDATA_TOKEN\"/g" netdata-helmchart/charts/netdata/values.yaml
sleep 1
sed -i "s/rooms: \"\"/rooms: \"$NETDATA_ROOMS\"/g" netdata-helmchart/charts/netdata/values.yaml
sleep 1
sed -i "s/accessmodes: ReadWriteOnce/accessmodes: $ACCESSMODE/g" netdata-helmchart/charts/netdata/values.yaml
sleep 1
sed -i "s/storageclass: \"-\"/storageclass: \"$STORAGE_CLASS\"/g" netdata-helmchart/charts/netdata/values.yaml

helm template netdata -f netdata-helmchart/charts/netdata/values.yaml netdata-helmchart/charts/netdata --namespace netdata > k8s/netdata/install.yaml
sleep 3
kubectl apply -f k8s/netdata/install.yaml
rm -rf netdata-helmchart
if [ ! -f /usr/bin/htpasswd ]; then sudo apt install apache2-utils; fi

echo "Begining creation of NetData Basic Auth Secret To Secure Its UI."
unset Netdata_Credentials
add_Netdata_credentials='y'
declare -A Netdata_Credentials
while [[ "$add_Netdata_credentials" == y ]]; do
  read -p 'Enter Netdata Username: ' netdata_username
  read -p 'Enter Netdata Password: ' netdata_password
  Netdata_Credentials[$netdata_username]+=$netdata_password
  add_Netdata_credentials='n'
done
echo -e "${CYAN}Your Netdata Username is: ${ENDCOLOR}" ${!Netdata_Credentials[@]}
echo -e "${CYAN}Your Netdata Password is: ${ENDCOLOR}" ${Netdata_Credentials[@]}
htpasswd -bnBC 12 "${!Netdata_Credentials[@]}" ${Netdata_Credentials[@]} | tr -d '\n' | printf "%s" "$(</dev/stdin)" | kubectl create secret generic netdata-basic-auth --from-file=auth=/dev/stdin -n netdata
unset Netdata_Credentials
sed -i "s/#//g" k8s/netdata/ingress-router.yaml
sed -i "s/example.com/$BASE_DOMAIN/g" k8s/netdata/ingress-router.yaml
kubectl apply -f k8s/netdata/ingress-router.yaml
echo -e "${GREEN}#####---Installation Successfully Completed!---#####${ENDCOLOR}"

#######----------------------------------------------------------------------#########
echo -e "${CYAN}Scanning API Image for Security Vulnerabilities${ENDCOLOR}"
docker scan $IMAGE_TAG
echo -e "${CYAN}Scanning MySQL Image for Security Vulnerabilities${ENDCOLOR}"
docker scan admintuts/mariadb:10.5.8-focal
echo -e "${GREEN}#####---Project Operations Successfully Completed!---#####${ENDCOLOR}"