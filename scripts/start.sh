#!/bin/bash

# ANALYTICA Framework - Startup Script
# Usage: ./start.sh [all|domain_name|--help]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_DIR/docker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Domain to port mapping
declare -A DOMAIN_PORTS=(
    ["repox"]=8000
    ["analizowanie"]=8001
    ["przeanalizuj"]=8002
    ["alerts"]=8003
    ["estymacja"]=8004
    ["retrospektywa"]=8005
    ["persony"]=8006
    ["specyfikacja"]=8007
    ["nisza"]=8008
    ["multiplan"]=8010
    ["planbudzetu"]=8011
    ["planinwestycji"]=8012
)

print_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    ANALYTICA Framework                        ║"
    echo "║              Multi-Domain Analytics Platform                  ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 all              - Start all services"
    echo "  $0 infra            - Start infrastructure only (DB, Redis, Nginx)"
    echo "  $0 <domain>         - Start specific domain API"
    echo "  $0 financial        - Start financial domains (multiplan, planbudzetu, planinwestycji)"
    echo "  $0 status           - Show status of all services"
    echo "  $0 logs <service>   - Show logs for service"
    echo "  $0 stop             - Stop all services"
    echo ""
    echo -e "${YELLOW}Available domains:${NC}"
    for domain in "${!DOMAIN_PORTS[@]}"; do
        echo "  - $domain (port ${DOMAIN_PORTS[$domain]})"
    done | sort
}

start_infra() {
    echo -e "${BLUE}Starting infrastructure...${NC}"
    cd "$DOCKER_DIR"
    docker-compose up -d postgres redis
    echo -e "${GREEN}Waiting for databases to be ready...${NC}"
    sleep 5
    docker-compose up -d nginx grafana prometheus
    echo -e "${GREEN}Infrastructure started!${NC}"
}

start_domain() {
    local domain=$1
    if [[ -z "${DOMAIN_PORTS[$domain]}" ]]; then
        echo -e "${RED}Unknown domain: $domain${NC}"
        print_usage
        exit 1
    fi
    
    echo -e "${BLUE}Starting API for ${domain}.pl on port ${DOMAIN_PORTS[$domain]}...${NC}"
    cd "$DOCKER_DIR"
    docker-compose up -d "api-$domain"
    echo -e "${GREEN}${domain}.pl started on port ${DOMAIN_PORTS[$domain]}${NC}"
}

start_all() {
    echo -e "${BLUE}Starting all services...${NC}"
    cd "$DOCKER_DIR"
    docker-compose up -d
    echo -e "${GREEN}All services started!${NC}"
}

start_financial() {
    echo -e "${BLUE}Starting financial domains...${NC}"
    start_infra
    start_domain "multiplan"
    start_domain "planbudzetu"
    start_domain "planinwestycji"
    echo -e "${GREEN}Financial domains started!${NC}"
}

show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    cd "$DOCKER_DIR"
    docker-compose ps
    
    echo ""
    echo -e "${YELLOW}Port Mapping:${NC}"
    echo "┌────────────────────┬──────────┬────────────────────────────────┐"
    echo "│ Domain             │ API Port │ URL                            │"
    echo "├────────────────────┼──────────┼────────────────────────────────┤"
    for domain in $(echo "${!DOMAIN_PORTS[@]}" | tr ' ' '\n' | sort); do
        printf "│ %-18s │ %-8s │ http://localhost:%-13s │\n" "${domain}.pl" "${DOMAIN_PORTS[$domain]}" "${DOMAIN_PORTS[$domain]}"
    done
    echo "└────────────────────┴──────────┴────────────────────────────────┘"
    
    echo ""
    echo -e "${YELLOW}Additional Services:${NC}"
    echo "  - Grafana:    http://localhost:3100"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis:      localhost:6379"
}

show_logs() {
    local service=$1
    if [[ -z "$service" ]]; then
        echo -e "${RED}Please specify a service name${NC}"
        exit 1
    fi
    cd "$DOCKER_DIR"
    docker-compose logs -f "$service"
}

stop_all() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    cd "$DOCKER_DIR"
    docker-compose down
    echo -e "${GREEN}All services stopped!${NC}"
}

# Main
print_header

case "${1:-}" in
    all)
        start_all
        show_status
        ;;
    infra)
        start_infra
        ;;
    financial)
        start_financial
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    stop)
        stop_all
        ;;
    --help|-h|"")
        print_usage
        ;;
    *)
        start_domain "$1"
        ;;
esac
