#!/bin/bash
# Docker permissions setup for k3d cluster creation

echo "Setting up Docker permissions for k3d cluster creation..."

# Check if docker group exists
if ! getent group docker > /dev/null 2>&1; then
    echo "Creating docker group..."
    sudo groupadd docker
fi

# Add current user to docker group
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

echo "Docker permissions setup complete!"
echo ""
echo "⚠️  IMPORTANT: You need to log out and log back in (or restart your terminal)"
echo "    for the group changes to take effect."
echo ""
echo "After logging back in, verify with:"
echo "  groups"
echo "  docker ps"
echo ""
echo "Then you can create the k3d cluster with:"
echo "  k3d cluster create alloy-kafka-dev --port \"8080:80@loadbalancer\" --port \"8443:443@loadbalancer\" --registry-create alloy-kafka-registry:0.0.0.0:5001 --agents 0 --servers 1"