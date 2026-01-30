#!/bin/bash
# K3d Cluster Validation Tests for Alloy-Kafka Development Environment

set -e

CLUSTER_NAME="alloy-kafka-dev"
REGISTRY_PORT="5001"
INGRESS_PORT="80"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test 1: k3d installation check
test_k3d_installation() {
    log_info "Testing k3d installation..."
    
    if command -v k3d >/dev/null 2>&1; then
        K3D_VERSION=$(k3d version | grep k3d | awk '{print $3}')
        log_info "k3d version $K3D_VERSION is installed ✓"
        return 0
    else
        log_error "k3d is not installed ✗"
        return 1
    fi
}

# Test 2: Docker environment check
test_docker_environment() {
    log_info "Testing Docker environment..."
    
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            DOCKER_VERSION=$(docker version --format '{{.Server.Version}}')
            log_info "Docker version $DOCKER_VERSION is running ✓"
            
            # Check BuildKit support
            if docker buildx version >/dev/null 2>&1; then
                log_info "Docker BuildKit support available ✓"
            else
                log_warn "Docker BuildKit support not available"
            fi
            return 0
        else
            log_error "Docker daemon is not running ✗"
            return 1
        fi
    else
        log_error "Docker is not installed ✗"
        return 1
    fi
}

# Test 3: Cluster creation validation
test_cluster_creation() {
    log_info "Testing cluster creation..."
    
    # Check if cluster exists
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_info "Cluster '$CLUSTER_NAME' exists ✓"
        
        # Check if cluster is running
        if k3d cluster list | grep "$CLUSTER_NAME" | grep -q "running"; then
            log_info "Cluster '$CLUSTER_NAME' is running ✓"
            return 0
        else
            log_error "Cluster '$CLUSTER_NAME' exists but not running ✗"
            return 1
        fi
    else
        log_error "Cluster '$CLUSTER_NAME' does not exist ✗"
        return 1
    fi
}

# Test 4: Kubectl connectivity check
test_kubectl_connectivity() {
    log_info "Testing kubectl connectivity..."
    
    if command -v kubectl >/dev/null 2>&1; then
        # Check if current context is the k3d cluster
        CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "none")
        if [[ "$CURRENT_CONTEXT" == "k3d-$CLUSTER_NAME" ]]; then
            log_info "kubectl context is set to k3d-$CLUSTER_NAME ✓"
            
            # Test cluster connectivity
            if kubectl cluster-info >/dev/null 2>&1; then
                log_info "kubectl can connect to cluster ✓"
                
                # Test node readiness
                READY_NODES=$(kubectl get nodes --no-headers | grep -c "Ready")
                TOTAL_NODES=$(kubectl get nodes --no-headers | wc -l)
                log_info "Cluster nodes: $READY_NODES/$TOTAL_NODES ready ✓"
                
                return 0
            else
                log_error "kubectl cannot connect to cluster ✗"
                return 1
            fi
        else
            log_error "kubectl context is not set to k3d-$CLUSTER_NAME (current: $CURRENT_CONTEXT) ✗"
            return 1
        fi
    else
        log_error "kubectl is not installed ✗"
        return 1
    fi
}

# Test 5: Local registry validation
test_local_registry() {
    log_info "Testing local registry..."
    
    # Check if registry is running
    if docker ps | grep -q "k3d-$CLUSTER_NAME-registry"; then
        log_info "Local registry container is running ✓"
        
        # Test registry connectivity
        if curl -s "http://localhost:$REGISTRY_PORT/v2/" >/dev/null 2>&1; then
            log_info "Local registry is accessible on port $REGISTRY_PORT ✓"
            return 0
        else
            log_error "Local registry is not accessible on port $REGISTRY_PORT ✗"
            return 1
        fi
    else
        log_error "Local registry container is not running ✗"
        return 1
    fi
}

# Test 6: Ingress controller validation
test_ingress_controller() {
    log_info "Testing ingress controller..."
    
    # Check if traefik (k3s default ingress) is running
    if kubectl get pods -n kube-system | grep -q "traefik"; then
        log_info "Traefik ingress controller is running ✓"
        
        # Check if ingress port is accessible
        if nc -z localhost $INGRESS_PORT 2>/dev/null; then
            log_info "Ingress controller is accessible on port $INGRESS_PORT ✓"
            return 0
        else
            log_error "Ingress controller is not accessible on port $INGRESS_PORT ✗"
            return 1
        fi
    else
        log_error "Traefik ingress controller is not running ✗"
        return 1
    fi
}

# Test 7: Helm installation check
test_helm_installation() {
    log_info "Testing Helm installation..."
    
    if command -v helm >/dev/null 2>&1; then
        HELM_VERSION=$(helm version --short 2>/dev/null | cut -d':' -f2 | tr -d ' ')
        log_info "Helm version $HELM_VERSION is installed ✓"
        
        # Check Helm repositories
        log_info "Checking Helm repositories..."
        helm repo list >/dev/null 2>&1 || log_warn "No Helm repositories configured"
        
        return 0
    else
        log_error "Helm is not installed ✗"
        return 1
    fi
}

# Test 8: Resource availability check
test_resource_availability() {
    log_info "Testing resource availability..."
    
    # Check available system resources
    TOTAL_RAM=$(free -h | awk '/^Mem:/ {print $2}')
    AVAILABLE_RAM=$(free -h | awk '/^Mem:/ {print $7}')
    log_info "System RAM: $TOTAL_RAM total, $AVAILABLE_RAM available"
    
    # Check disk space
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 90 ]; then
        log_info "Disk usage: $DISK_USAGE% (sufficient) ✓"
        return 0
    else
        log_warn "Disk usage: $DISK_USAGE% (may be insufficient)"
        return 1
    fi
}

# Main test runner
run_all_tests() {
    log_info "Starting k3d cluster validation tests..."
    echo "=================================================="
    
    TOTAL_TESTS=8
    PASSED_TESTS=0
    
    # Run all tests
    test_functions=(
        "test_k3d_installation"
        "test_docker_environment"
        "test_cluster_creation"
        "test_kubectl_connectivity"
        "test_local_registry"
        "test_ingress_controller"
        "test_helm_installation"
        "test_resource_availability"
    )
    
    for test_func in "${test_functions[@]}"; do
        echo ""
        if $test_func; then
            ((PASSED_TESTS++))
        fi
    done
    
    echo ""
    echo "=================================================="
    log_info "Test Results: $PASSED_TESTS/$TOTAL_TESTS tests passed"
    
    if [ "$PASSED_TESTS" -eq "$TOTAL_TESTS" ]; then
        log_info "All tests passed! Cluster is ready for Alloy-Kafka development ✓"
        exit 0
    else
        log_error "Some tests failed. Please check the issues above ✗"
        exit 1
    fi
}

# Run tests if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    run_all_tests
fi