# Fora Infrastructure Overview

## Introduction

Fora is a full-stack application deployed on **Azure Web Apps**, leveraging containerized deployment through Docker and Azure Container Registry (ACR). The infrastructure is designed to support a Next.js frontend and a FastAPI backend, with Supabase as the primary database and authentication provider. This document provides a comprehensive overview of the deployment architecture, CI/CD workflows, and integration patterns for developers new to the codebase.

## Architecture Overview

### Azure Web Apps Deployment

The application runs on two separate **Azure Web Apps** instances hosted in the **Canada Central** region:

1. **fora-web** - Frontend application (Next.js)
2. **fora-prod** - Backend API (FastAPI/Python)

Both applications are deployed as **Linux containers** on a shared **App Service Plan** (`fora`) within the resource group `fora-rg`. This architecture provides cost efficiency while maintaining separation of concerns between frontend and backend services.

### Container Registry

All container images are stored in **Azure Container Registry (ACR)** named `xfora.azurecr.io`. The registry uses managed identity authentication to allow Web Apps to pull images securely without storing passwords. Two primary images are maintained:

- `fora-client:latest` - Next.js frontend container
- `fora-api:latest` - FastAPI backend container

### Identity and Access Management

The infrastructure uses a **User-Assigned Managed Identity** (`ua-id-abd8`) to authenticate Web Apps with the container registry. This eliminates the need for credential management and provides a more secure authentication mechanism. The managed identity has the necessary permissions to pull container images from ACR and is configured at the Web App level through the ARM templates.

## Infrastructure as Code (ARM Templates)

The infrastructure is defined using two Azure Resource Manager (ARM) templates located in the `devops/` directory:

### Backend Template (fora-prod-arm.json)

This template defines the `fora-prod` Web App resource with the following key configurations:

- **Linux container runtime** with Docker support (`kind: app,linux,container`)
- **Container image**: Configured to pull `xfora.azurecr.io/fora-api:latest`
- **Managed identity authentication** for ACR access
- **HTTPS enforcement** with TLS 1.2 minimum version
- **Disabled FTP access** for enhanced security
- **Load balancing**: Configured with LeastRequests algorithm
- **Auto-scaling**: Supports elastic scaling based on demand

The template also configures:
- Publishing credentials policies (FTP and SCM disabled)
- Web configuration with Linux virtual paths
- IP security restrictions (currently allows all traffic)
- Hostname bindings for the Azure-provided domain

### Frontend Template (fora-web-arm.json)

This template defines the `fora-web` Web App with similar security configurations but uses **site containers** for the Next.js application:

- **Container configuration**: Uses `sitecontainers` Linux runtime
- **Main container**: Defined as a site container resource with target port 3000
- **Image source**: `xfora.azurecr.io/fora-client:latest`
- **Environment variables**: Configured through the deployment workflow (Supabase URLs, API endpoints, etc.)
- **Same security hardening**: HTTPS only, TLS 1.2, disabled FTP

The frontend uses a **site container** approach where the container is explicitly defined as a child resource, allowing for more granular control over environment variables and port mappings.

## Continuous Integration and Deployment

### CI/CD Pipeline Architecture

The deployment process uses **GitHub Actions** with two separate workflows that trigger on pushes to the `main` branch:

1. **Backend Deploy** (`.github/workflows/backend-deploy.yml`)
2. **Frontend Deploy** (`.github/workflows/frontend-deploy.yml`)

Both workflows follow a similar pattern but are path-filtered to only run when relevant code changes occur.

### Backend Deployment Workflow

The backend workflow (`backend-deploy.yml`) consists of two jobs:

**Build and Push Job:**
- Checks out the repository code
- Authenticates with ACR using stored credentials (`ACR_USERNAME` and `ACR_PASSWORD`)
- Sets up Docker Buildx for optimized multi-platform builds
- Builds the Docker image from `server/Dockerfile`
- Pushes to `xfora.azurecr.io/fora-api:latest`
- Utilizes registry caching to speed up subsequent builds

**Deploy Job:**
- Authenticates with Azure using service principal credentials
- Enables continuous deployment on the Web App
- Configures the deployment container settings
- Restarts the Web App to pull and run the new container image
- Verifies the deployment was successful

### Frontend Deployment Workflow

The frontend workflow (`frontend-deploy.yml`) follows the same pattern with frontend-specific configurations:

**Build and Push Job:**
- Builds the Next.js application with build-time environment variables:
  - `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
  - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` - Public anon key for client-side auth
  - `NEXT_PUBLIC_API_BASE_URL` - Backend API endpoint (fora-prod URL)
  - `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` - For map features
- Pushes to `xfora.azurecr.io/fora-client:latest`

**Deploy Job:**
- Same deployment pattern as backend
- Restarts `fora-web` to pull the updated container

### Secrets Management

The workflows rely on GitHub Secrets for sensitive credentials:

- `ACR_USERNAME` and `ACR_PASSWORD` - Container registry authentication
- `AZURE_CREDENTIALS` - Service principal JSON for Azure CLI authentication
- Supabase credentials and API keys for the frontend build
- All secrets are injected at build time or runtime as appropriate

## Supabase Integration

Supabase serves as the **primary database and authentication provider** for the Fora application. It is a managed PostgreSQL database with built-in authentication, real-time subscriptions, and RESTful API generation.

### Backend Integration

The FastAPI backend connects to Supabase using the Python `supabase-py` client library with cached client instances (`get_supabase_client()` and `get_service_role_client()`) defined in `server/app/core/database.py`. Configuration is loaded from environment variables (`SUPABASE_URL` and `SUPABASE_KEY`).

### Frontend Integration

The Next.js frontend uses `@supabase/ssr` with `createBrowserClient()` for client-side operations, utilizing public environment variables (`NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`) that are safe for browser exposure.

### Key Use Cases

Both frontend and backend use Supabase for user authentication, real-time chat, task/listing management, and ML training data storage. Row-level security (RLS) policies enforce data access controls at the database level. All schemas are version-controlled in the `docs/` directory.

## Deployment Process

### Typical Deployment Flow

1. **Developer pushes code** to the `main` branch
2. **GitHub Actions detects changes** in `server/` or `client/` directories
3. **Docker image is built** with all dependencies and application code
4. **Image is pushed to ACR** with the `latest` tag
5. **Azure Web App is configured** to enable continuous deployment
6. **Web App pulls the new image** from ACR using managed identity
7. **Application restarts** with the new version
8. **Health checks verify** the deployment was successful

### Rollback Strategy

If a deployment fails, the previous container image remains available in ACR. Rollback can be performed by:
- Manually deploying a specific image tag through Azure Portal or CLI
- Reverting the code changes and re-triggering the workflow
- Using Azure's deployment slot feature (not currently configured)

## Security Considerations

### Network Security

- **HTTPS enforcement**: All traffic is forced to HTTPS with minimum TLS 1.2
- **Public network access**: Currently enabled for both Web Apps
- **IP restrictions**: Set to allow all (can be restricted to specific IPs/ranges)
- **FTP disabled**: Publishing credentials are restricted to prevent FTP access

### Authentication and Authorization

- **Managed identities**: Used for ACR access, eliminating stored credentials
- **Supabase RLS**: Row-level security policies enforce data access at the database level
- **Service role key**: Kept secret and only used in backend for admin operations
- **API authentication**: Protected routes use Supabase JWT verification

### Secrets Management

- **GitHub Secrets**: All sensitive credentials stored securely
- **Environment variables**: Runtime secrets injected into containers
- **No hardcoded credentials**: All configuration externalized
- **.env files**: Used locally but never committed to version control

## Cost and Scaling

The current infrastructure uses:
- **Shared App Service Plan** for cost efficiency
- **Standard tier Web Apps** with auto-scaling capabilities
- **Basic ACR tier** for container storage
- **Supabase free/pro tier** depending on usage

Scaling options:
- **Vertical scaling**: Upgrade the App Service Plan for more CPU/memory
- **Horizontal scaling**: Configure auto-scaling rules based on CPU/memory metrics
- **Database scaling**: Upgrade Supabase tier for higher connections and storage

## Monitoring and Observability

Azure provides built-in monitoring through:
- **Application Insights**: Can be configured for detailed telemetry
- **App Service logs**: HTTP logs, application logs, and deployment logs
- **Container logs**: Stdout/stderr from running containers
- **Metrics**: CPU, memory, HTTP request rates, and response times

Currently, basic logging is enabled. For production, consider:
- Enabling Application Insights for distributed tracing
- Configuring log retention policies
- Setting up alerts for critical metrics
- Implementing health check endpoints

## Development Workflow

### Local Development

Developers can run the application locally using:
- **Docker Compose**: Spin up both frontend and backend containers
- **Native development**: Run Next.js and FastAPI directly with local Python/Node
- **Local Supabase**: Optional local Supabase instance for offline development

### Testing Before Deployment

- **Pull requests**: Should include tests and linting
- **Staging environment**: Can be created by duplicating ARM templates with different names
- **Feature branches**: Deploy to separate Web Apps for testing

### Environment Parity

The Dockerfiles ensure that local, CI, and production environments run the same code with identical dependencies, following the twelve-factor app methodology.

## Conclusion

The Fora infrastructure leverages Azure Web Apps for simplified container orchestration, eliminating the need for Kubernetes while maintaining flexibility and scalability. The use of ARM templates ensures reproducible infrastructure deployments, while GitHub Actions provides automated CI/CD. Supabase integration provides a robust backend-as-a-service solution for authentication, real-time features, and PostgreSQL database management. This architecture balances developer productivity, operational simplicity, and production reliability.