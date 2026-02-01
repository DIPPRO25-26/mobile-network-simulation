#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECURITY_DIR="$PROJECT_ROOT/security"

CERTS_DIR="$SECURITY_DIR/certs"
KEYS_DIR="$SECURITY_DIR/keys"

echo "🔐 Generating security certificates and keys..."

mkdir -p "$CERTS_DIR"
mkdir -p "$KEYS_DIR"
mkdir -p "$SECURITY_DIR/audit"

echo "📝 Generating HMAC secret key..."
HMAC_KEY=$(openssl rand -base64 32)
echo "$HMAC_KEY" > "$KEYS_DIR/hmac_secret.key"
chmod 600 "$KEYS_DIR/hmac_secret.key"
echo "✅ HMAC key saved to security/keys/hmac_secret.key"

echo "🏢 Generating Certificate Authority..."

mkdir -p "$CERTS_DIR/ca"

openssl genrsa -out "$CERTS_DIR/ca/ca.key" 4096
openssl req -new -x509 -days 3650 \
  -key "$CERTS_DIR/ca/ca.key" \
  -out "$CERTS_DIR/ca/ca.crt" \
  -subj "//C=HR/ST=Zagreb/L=Zagreb/O=FER/OU=Mobile Network Simulation/CN=Mobile-Network-CA"

echo "✅ CA certificate generated"

generate_cert () {
  SERVICE_NAME=$1
  SERVICE_DIR="$CERTS_DIR/$SERVICE_NAME"

  echo "🔑 Generating certificate for $SERVICE_NAME"

  mkdir -p "$SERVICE_DIR"

  openssl genrsa -out "$SERVICE_DIR/tls.key" 2048

  cat > "$SERVICE_DIR/openssl.cnf" <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
C = HR
ST = Zagreb
L = Zagreb
O = FER
OU = $SERVICE_NAME
CN = $SERVICE_NAME

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $SERVICE_NAME
EOF

  openssl req -new \
    -key "$SERVICE_DIR/tls.key" \
    -out "$SERVICE_DIR/tls.csr" \
    -config "$SERVICE_DIR/openssl.cnf"

  openssl x509 -req -days 365 \
    -in "$SERVICE_DIR/tls.csr" \
    -CA "$CERTS_DIR/ca/ca.crt" \
    -CAkey "$CERTS_DIR/ca/ca.key" \
    -CAcreateserial \
    -out "$SERVICE_DIR/tls.crt" \
    -extensions req_ext \
    -extfile "$SERVICE_DIR/openssl.cnf"

  rm "$SERVICE_DIR/tls.csr" "$SERVICE_DIR/openssl.cnf"
}

generate_cert "central-backend"

# Keystore (Spring Boot zahtijeva)
openssl pkcs12 -export \
  -in "$CERTS_DIR/central-backend/tls.crt" \
  -inkey "$CERTS_DIR/central-backend/tls.key" \
  -out "$CERTS_DIR/central-backend/keystore.p12" \
  -name central-backend \
  -password pass:changeit

# Truststore
keytool -importcert \
  -noprompt \
  -alias root-ca \
  -file "$CERTS_DIR/ca/ca.crt" \
  -keystore "$CERTS_DIR/central-backend/truststore.p12" \
  -storepass changeit


generate_cert "bts-service"
generate_cert "analytics"
generate_cert "simulator"

chmod 600 "$CERTS_DIR"/**/*.key
chmod 600 "$KEYS_DIR"/*.key

touch "$CERTS_DIR/.gitkeep"
touch "$KEYS_DIR/.gitkeep"
touch "$SECURITY_DIR/audit/.gitkeep"

echo ""
echo "✅ All certificates and keys generated successfully!"
echo ""
echo "📁 Generated:"
echo " - Root CA: security/certs/ca/ca.crt"
echo " - Central Backend: cert + keystore + truststore"
echo " - Clients: bts-service, analytics, simulator"
echo " - HMAC key: security/keys/hmac_secret.key"
echo ""
echo "⚠️  DO NOT COMMIT generated certs or keys."
echo "💡 Update .env with:"
echo "   HMAC_SECRET_KEY=$HMAC_KEY"
echo ""