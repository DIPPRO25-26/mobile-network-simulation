#!/bin/bash

# Generate security certificates and keys for mobile network simulation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECURITY_DIR="$PROJECT_ROOT/security"

echo "🔐 Generating security certificates and keys..."

# Create directories
mkdir -p "$SECURITY_DIR/certs"
mkdir -p "$SECURITY_DIR/keys"
mkdir -p "$SECURITY_DIR/audit"

# Generate HMAC secret key
echo "📝 Generating HMAC secret key..."
HMAC_KEY=$(openssl rand -base64 32)
echo "$HMAC_KEY" > "$SECURITY_DIR/keys/hmac_secret.key"
chmod 600 "$SECURITY_DIR/keys/hmac_secret.key"
echo "✅ HMAC key saved to security/keys/hmac_secret.key"

# Generate CA (Certificate Authority)
echo "🏢 Generating Certificate Authority..."
openssl genrsa -out "$SECURITY_DIR/certs/ca-key.pem" 4096
openssl req -new -x509 -days 365 -key "$SECURITY_DIR/certs/ca-key.pem" \
    -out "$SECURITY_DIR/certs/ca-cert.pem" \
    -subj "/C=HR/ST=Zagreb/L=Zagreb/O=FER/OU=Mobile Network Simulation/CN=Mobile-Network-CA"
echo "✅ CA certificate generated"

# Generate server certificate (for central backend)
echo "🖥️  Generating server certificate..."
openssl genrsa -out "$SECURITY_DIR/certs/server-key.pem" 4096
openssl req -new -key "$SECURITY_DIR/certs/server-key.pem" \
    -out "$SECURITY_DIR/certs/server.csr" \
    -subj "/C=HR/ST=Zagreb/L=Zagreb/O=FER/OU=Central Backend/CN=central-backend"
openssl x509 -req -days 365 -in "$SECURITY_DIR/certs/server.csr" \
    -CA "$SECURITY_DIR/certs/ca-cert.pem" \
    -CAkey "$SECURITY_DIR/certs/ca-key.pem" \
    -CAcreateserial \
    -out "$SECURITY_DIR/certs/server-cert.pem"
rm "$SECURITY_DIR/certs/server.csr"
echo "✅ Server certificate generated"

# Generate client certificates (for BTS services)
for i in 1 2 3; do
    echo "📡 Generating BTS-$i client certificate..."
    openssl genrsa -out "$SECURITY_DIR/certs/bts-$i-key.pem" 4096
    openssl req -new -key "$SECURITY_DIR/certs/bts-$i-key.pem" \
        -out "$SECURITY_DIR/certs/bts-$i.csr" \
        -subj "/C=HR/ST=Zagreb/L=Zagreb/O=FER/OU=BTS Service/CN=bts-$i"
    openssl x509 -req -days 365 -in "$SECURITY_DIR/certs/bts-$i.csr" \
        -CA "$SECURITY_DIR/certs/ca-cert.pem" \
        -CAkey "$SECURITY_DIR/certs/ca-key.pem" \
        -CAcreateserial \
        -out "$SECURITY_DIR/certs/bts-$i-cert.pem"
    rm "$SECURITY_DIR/certs/bts-$i.csr"
done
echo "✅ BTS client certificates generated"

# Set proper permissions
chmod 600 "$SECURITY_DIR/certs/"*.pem
chmod 600 "$SECURITY_DIR/keys/"*.key

# Create .gitkeep files
touch "$SECURITY_DIR/certs/.gitkeep"
touch "$SECURITY_DIR/keys/.gitkeep"
touch "$SECURITY_DIR/audit/.gitkeep"

echo ""
echo "✅ All certificates and keys generated successfully!"
echo ""
echo "📁 Generated files:"
echo "   - HMAC key: security/keys/hmac_secret.key"
echo "   - CA certificate: security/certs/ca-cert.pem"
echo "   - Server certificate: security/certs/server-cert.pem"
echo "   - BTS certificates: security/certs/bts-{1,2,3}-cert.pem"
echo ""
echo "⚠️  IMPORTANT: These are development certificates only!"
echo "   Never commit these files to version control."
echo "   For production, use proper CA-signed certificates."
echo ""
echo "💡 Update your .env file with the HMAC key:"
echo "   HMAC_SECRET_KEY=$HMAC_KEY"
