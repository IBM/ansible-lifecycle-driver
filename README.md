# ansible-lifecycle-driver
Lifecycle driver implementation that uses Ansible to execute operations


openssl req -newkey rsa:2048 -nodes -keyout ald-tls.key -x509 -days 3650 -out alf-tls.cer -subj "/CN=ansible-lifecycle-driver"
kubectl create secret tls ald-tls --key ald-tls.key --cert ald-tls.cer