"""
ANALYTICA DSL - Deployment & CI/CD Atoms
=========================================
Atoms for deploying DSL pipelines and applications to various platforms.

Supports:
- Containers: Docker, Podman
- Orchestration: Kubernetes, Docker Compose, Helm
- CI/CD: GitHub Actions, GitLab CI, Jenkins, CircleCI
- Cloud: AWS, Azure, GCP, Vercel, Netlify
- Platforms: Desktop (Electron, Tauri), Mobile (React Native, Flutter), Web
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.registry import AtomRegistry


def _deploy_result(config: Dict, metadata: Dict) -> Dict:
    """Wrap deployment result with metadata"""
    return {
        "config": config,
        "deploy": metadata,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "ready"
    }


def _ensure_pipeline_state(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict) and "views" in data:
        state = dict(data)
        state.setdefault("deployments", [])
        return state
    return {"data": data, "views": [], "deployments": []}


def _add_deployment(ctx, config: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    state = _ensure_pipeline_state(ctx.get_data())
    entry = {
        "platform": metadata.get("platform"),
        "status": metadata.get("status") or "ready",
        "access_uri": metadata.get("access_uri"),
        "launch_uri": metadata.get("launch_uri"),
        "url": metadata.get("url") or metadata.get("access_uri"),
        "commands": config.get("commands", {}),
        "config": config,
    }
    deployments = list(state.get("deployments") or [])
    deployments.append(entry)
    state["deployments"] = deployments

    out = dict(state)
    out["config"] = config
    out["deploy"] = metadata
    out["generated_at"] = datetime.utcnow().isoformat()
    out["status"] = "ready"
    return out


# ============================================================
# CONTAINER ATOMS
# ============================================================

@AtomRegistry.register("deploy", "docker")
def deploy_docker(ctx, **params) -> Dict:
    """
    Generate Docker deployment configuration.
    
    Usage:
        deploy.docker(image="analytica/app", tag="latest", port=8000)
        deploy.docker(dockerfile="Dockerfile.prod", build=true)
    """
    data = ctx.get_data()
    image = params.get("image", params.get("_arg0", "app"))
    tag = params.get("tag", "latest")
    port = params.get("port", 8000)
    host = params.get("host", "localhost")
    access_uri = params.get("access_uri") or params.get("uri") or f"http://{host}:{port}"
    dockerfile = params.get("dockerfile", "Dockerfile")
    build = params.get("build", False)
    env = params.get("env", {})
    volumes = params.get("volumes", [])
    
    config = {
        "type": "docker",
        "image": f"{image}:{tag}",
        "dockerfile": dockerfile,
        "port": port,
        "env": env,
        "volumes": volumes,
        "commands": {
            "build": f"docker build -t {image}:{tag} -f {dockerfile} .",
            "run": f"docker run -d -p {port}:{port} {image}:{tag}",
            "push": f"docker push {image}:{tag}",
            "stop": f"docker stop $(docker ps -q --filter ancestor={image}:{tag})"
        }
    }
    
    if data is not None:
        config["pipeline"] = data
    
    ctx.log(f"Docker config generated: {image}:{tag}")
    return _add_deployment(ctx, config, {"platform": "docker", "image": image, "access_uri": access_uri, "launch_uri": access_uri})


@AtomRegistry.register("deploy", "compose")
def deploy_compose(ctx, **params) -> Dict:
    """
    Generate Docker Compose configuration.
    
    Usage:
        deploy.compose(services=["api", "db", "redis"], file="docker-compose.prod.yml")
    """
    data = ctx.get_data()
    services = params.get("services", params.get("_arg0", ["app"]))
    file = params.get("file", "docker-compose.yml")
    host = params.get("host", "localhost")
    port = params.get("port")
    access_uri = params.get("access_uri") or params.get("uri") or (f"http://{host}:{port}" if port else None)
    
    config = {
        "type": "docker-compose",
        "file": file,
        "services": services,
        "commands": {
            "up": f"docker-compose -f {file} up -d",
            "down": f"docker-compose -f {file} down",
            "logs": f"docker-compose -f {file} logs -f",
            "build": f"docker-compose -f {file} build"
        }
    }
    
    ctx.log(f"Docker Compose config: {file}")
    return _add_deployment(ctx, config, {"platform": "compose", "services": services, "access_uri": access_uri, "launch_uri": access_uri})


# ============================================================
# KUBERNETES ATOMS
# ============================================================

@AtomRegistry.register("deploy", "kubernetes")
def deploy_kubernetes(ctx, **params) -> Dict:
    """
    Generate Kubernetes deployment configuration.
    
    Usage:
        deploy.kubernetes(namespace="prod", replicas=3, image="app:v1")
        deploy.kubernetes(manifest="k8s/", apply=true)
    """
    data = ctx.get_data()
    namespace = params.get("namespace", "default")
    replicas = params.get("replicas", 1)
    image = params.get("image", params.get("_arg0", "app:latest"))
    manifest = params.get("manifest", "k8s/")
    ingress_host = params.get("ingress_host")
    access_uri = params.get("access_uri") or params.get("uri") or (f"https://{ingress_host}" if ingress_host else None)
    resources = params.get("resources", {"cpu": "100m", "memory": "128Mi"})
    
    config = {
        "type": "kubernetes",
        "namespace": namespace,
        "replicas": replicas,
        "image": image,
        "manifest_path": manifest,
        "resources": resources,
        "commands": {
            "apply": f"kubectl apply -f {manifest} -n {namespace}",
            "delete": f"kubectl delete -f {manifest} -n {namespace}",
            "status": f"kubectl get pods -n {namespace}",
            "logs": f"kubectl logs -f -l app=analytica -n {namespace}",
            "scale": f"kubectl scale deployment/app --replicas={replicas} -n {namespace}"
        }
    }
    
    ctx.log(f"Kubernetes config: {namespace}, replicas={replicas}")
    return _add_deployment(ctx, config, {"platform": "kubernetes", "namespace": namespace, "access_uri": access_uri, "launch_uri": access_uri})


@AtomRegistry.register("deploy", "helm")
def deploy_helm(ctx, **params) -> Dict:
    """
    Generate Helm chart deployment.
    
    Usage:
        deploy.helm(chart="analytica", release="prod", values="values-prod.yaml")
    """
    chart = params.get("chart", params.get("_arg0", "analytica"))
    release = params.get("release", "prod")
    namespace = params.get("namespace", "default")
    access_uri = params.get("access_uri") or params.get("uri")
    values = params.get("values", "values.yaml")
    
    config = {
        "type": "helm",
        "chart": chart,
        "release": release,
        "namespace": namespace,
        "values": values,
        "commands": {
            "install": f"helm install {release} {chart} -f {values} -n {namespace}",
            "upgrade": f"helm upgrade {release} {chart} -f {values} -n {namespace}",
            "uninstall": f"helm uninstall {release} -n {namespace}",
            "status": f"helm status {release} -n {namespace}"
        }
    }
    
    ctx.log(f"Helm chart: {chart}, release={release}")
    return _add_deployment(ctx, config, {"platform": "helm", "chart": chart, "access_uri": access_uri, "launch_uri": access_uri})


# ============================================================
# CI/CD ATOMS
# ============================================================

@AtomRegistry.register("deploy", "github_actions")
def deploy_github_actions(ctx, **params) -> Dict:
    """
    Generate GitHub Actions workflow.
    
    Usage:
        deploy.github_actions(workflow="deploy", triggers=["push", "pull_request"])
    """
    workflow = params.get("workflow", params.get("_arg0", "deploy"))
    triggers = params.get("triggers", ["push"])
    access_uri = params.get("access_uri") or params.get("uri")
    branches = params.get("branches", ["main"])
    jobs = params.get("jobs", ["build", "test", "deploy"])
    
    config = {
        "type": "github_actions",
        "workflow": workflow,
        "file": f".github/workflows/{workflow}.yml",
        "triggers": triggers,
        "branches": branches,
        "jobs": jobs
    }
    
    ctx.log(f"GitHub Actions workflow: {workflow}")
    return _add_deployment(ctx, config, {"platform": "github_actions", "workflow": workflow, "access_uri": access_uri, "launch_uri": access_uri})


@AtomRegistry.register("deploy", "gitlab_ci")
def deploy_gitlab_ci(ctx, **params) -> Dict:
    """
    Generate GitLab CI configuration.
    
    Usage:
        deploy.gitlab_ci(stages=["build", "test", "deploy"])
    """
    stages = params.get("stages", params.get("_arg0", ["build", "test", "deploy"]))
    
    config = {
        "type": "gitlab_ci",
        "file": ".gitlab-ci.yml",
        "stages": stages
    }
    
    ctx.log(f"GitLab CI: stages={stages}")
    return _deploy_result(config, {"platform": "gitlab_ci"})


@AtomRegistry.register("deploy", "jenkins")
def deploy_jenkins(ctx, **params) -> Dict:
    """
    Generate Jenkins pipeline.
    
    Usage:
        deploy.jenkins(pipeline="Jenkinsfile", agents=["docker"])
    """
    pipeline = params.get("pipeline", "Jenkinsfile")
    agents = params.get("agents", ["any"])
    stages = params.get("stages", ["Build", "Test", "Deploy"])
    
    config = {
        "type": "jenkins",
        "file": pipeline,
        "agents": agents,
        "stages": stages
    }
    
    ctx.log(f"Jenkins pipeline: {pipeline}")
    return _deploy_result(config, {"platform": "jenkins"})


# ============================================================
# CLOUD PLATFORM ATOMS
# ============================================================

@AtomRegistry.register("deploy", "aws")
def deploy_aws(ctx, **params) -> Dict:
    """
    Deploy to AWS (ECS, Lambda, EC2).
    
    Usage:
        deploy.aws(service="ecs", cluster="prod", region="eu-central-1")
        deploy.aws(service="lambda", function="handler")
    """
    service = params.get("service", params.get("_arg0", "ecs"))
    region = params.get("region", "eu-central-1")
    cluster = params.get("cluster", "default")
    
    config = {
        "type": "aws",
        "service": service,
        "region": region,
        "cluster": cluster,
        "commands": {
            "deploy": f"aws ecs update-service --cluster {cluster} --service app --force-new-deployment",
            "status": f"aws ecs describe-services --cluster {cluster} --services app"
        }
    }
    
    ctx.log(f"AWS {service} config: region={region}")
    return _deploy_result(config, {"platform": "aws", "service": service})


@AtomRegistry.register("deploy", "vercel")
def deploy_vercel(ctx, **params) -> Dict:
    """
    Deploy to Vercel.
    
    Usage:
        deploy.vercel(project="my-app", prod=true)
    """
    project = params.get("project", params.get("_arg0", "app"))
    prod = params.get("prod", False)
    
    config = {
        "type": "vercel",
        "project": project,
        "production": prod,
        "commands": {
            "deploy": f"vercel {'--prod' if prod else ''}",
            "logs": "vercel logs",
            "env": "vercel env pull"
        }
    }
    
    ctx.log(f"Vercel deploy: {project}")
    return _deploy_result(config, {"platform": "vercel", "project": project})


@AtomRegistry.register("deploy", "netlify")
def deploy_netlify(ctx, **params) -> Dict:
    """
    Deploy to Netlify.
    
    Usage:
        deploy.netlify(site="my-site", prod=true)
    """
    site = params.get("site", params.get("_arg0", "app"))
    prod = params.get("prod", False)
    
    config = {
        "type": "netlify",
        "site": site,
        "production": prod,
        "commands": {
            "deploy": f"netlify deploy {'--prod' if prod else ''}",
            "status": "netlify status"
        }
    }
    
    ctx.log(f"Netlify deploy: {site}")
    return _deploy_result(config, {"platform": "netlify", "site": site})


# ============================================================
# PLATFORM TARGET ATOMS
# ============================================================

@AtomRegistry.register("deploy", "web")
def deploy_web(ctx, **params) -> Dict:
    """
    Configure web application deployment.
    
    Usage:
        deploy.web(framework="react", build="npm run build", output="dist")
    """
    data = ctx.get_data()
    framework = params.get("framework", params.get("_arg0", "react"))
    build_cmd = params.get("build", "npm run build")
    output = params.get("output", "dist")
    host = params.get("host", "localhost")
    port = params.get("port", 3000)
    base_path = params.get("path", "/")
    access_uri = params.get("access_uri") or params.get("uri") or f"http://{host}:{port}{base_path}".rstrip('/')
    
    config = {
        "type": "web",
        "framework": framework,
        "build": build_cmd,
        "output": output,
        "pipeline": data
    }
    
    ctx.log(f"Web deploy: {framework}")
    return _add_deployment(ctx, config, {"platform": "web", "framework": framework, "access_uri": access_uri, "launch_uri": access_uri})


@AtomRegistry.register("deploy", "mobile")
def deploy_mobile(ctx, **params) -> Dict:
    """
    Configure mobile application deployment.
    
    Usage:
        deploy.mobile(framework="react-native", platforms=["ios", "android"])
        deploy.mobile(framework="flutter", release=true)
    """
    data = ctx.get_data()
    framework = params.get("framework", params.get("_arg0", "react-native"))
    platforms = params.get("platforms", ["ios", "android"])
    release = params.get("release", False)
    host = params.get("host", "localhost")
    dev_port = params.get("dev_port", 8081)
    app_scheme = params.get("scheme", "analytica")
    access_uri = params.get("access_uri") or params.get("uri") or f"{app_scheme}://"
    launch_uri = params.get("launch_uri") or f"http://{host}:{dev_port}"
    
    config = {
        "type": "mobile",
        "framework": framework,
        "platforms": platforms,
        "release": release,
        "pipeline": data,
        "commands": {
            "ios": "npx react-native run-ios" if framework == "react-native" else "flutter run -d ios",
            "android": "npx react-native run-android" if framework == "react-native" else "flutter run -d android",
            "build_ios": "npx react-native build-ios --configuration Release" if framework == "react-native" else "flutter build ios",
            "build_android": "cd android && ./gradlew assembleRelease" if framework == "react-native" else "flutter build apk"
        }
    }
    
    ctx.log(f"Mobile deploy: {framework}, platforms={platforms}")
    return _add_deployment(ctx, config, {"platform": "mobile", "framework": framework, "access_uri": access_uri, "launch_uri": launch_uri})


@AtomRegistry.register("deploy", "desktop")
def deploy_desktop(ctx, **params) -> Dict:
    """
    Configure desktop application deployment.
    
    Usage:
        deploy.desktop(framework="electron", platforms=["win", "mac", "linux"])
        deploy.desktop(framework="tauri", release=true)
        deploy.desktop(framework="electron", project_dir="/path/to/project")
    """
    import urllib.parse as _urlparse
    import os as _os
    
    data = ctx.get_data()
    framework = params.get("framework", params.get("_arg0", "electron"))
    platforms = params.get("platforms", ["win", "mac", "linux"])
    release = params.get("release", False)
    default_url = _os.getenv("DESKTOP_DEFAULT_URL", "http://localhost:18000")
    url = params.get("url", default_url)
    project_dir = params.get("project_dir", params.get("dir", ""))
    access_uri = params.get("access_uri") or params.get("uri") or url
    
    if params.get("launch_uri"):
        launch_uri = params["launch_uri"]
    elif project_dir:
        launch_uri = f"analytica://desktop/run?dir={_urlparse.quote(project_dir)}&url={_urlparse.quote(url)}"
    else:
        launch_uri = "npm start"
    
    config = {
        "type": "desktop",
        "framework": framework,
        "platforms": platforms,
        "release": release,
        "url": url,
        "project_dir": project_dir,
        "pipeline": data,
        "commands": {
            "dev": "npm run electron:dev" if framework == "electron" else "npm run tauri dev",
            "build": "npm run electron:build" if framework == "electron" else "npm run tauri build",
            "build_win": "npm run electron:build -- --win" if framework == "electron" else "npm run tauri build -- --target x86_64-pc-windows-msvc",
            "build_mac": "npm run electron:build -- --mac" if framework == "electron" else "npm run tauri build -- --target x86_64-apple-darwin",
            "build_linux": "npm run electron:build -- --linux" if framework == "electron" else "npm run tauri build -- --target x86_64-unknown-linux-gnu"
        }
    }
    
    ctx.log(f"Desktop deploy: {framework}, platforms={platforms}, url={url}")
    return _add_deployment(ctx, config, {"platform": "desktop", "framework": framework, "url": url, "access_uri": access_uri, "launch_uri": launch_uri})


# ============================================================
# LAUNCH ATOMS
# ============================================================

@AtomRegistry.register("deploy", "launch")
def deploy_launch(ctx, **params) -> Dict:
    """
    Launch deployed application using URI scheme.
    
    Usage:
        deploy.launch(platform="desktop", dir="/path/to/project")
        deploy.launch(uri="analytica://desktop/run?dir=/tmp")
        deploy.launch(platform="web", url="http://localhost:3000")
    """
    import subprocess
    import urllib.parse as _urlparse
    import os as _os
    
    data = ctx.get_data()
    platform = params.get("platform", params.get("_arg0", "desktop"))
    uri = params.get("uri", "")
    project_dir = params.get("dir", params.get("project_dir", ""))
    default_url = _os.getenv("DESKTOP_DEFAULT_URL", "http://localhost:18000")
    url = params.get("url", default_url)
    
    if not uri:
        if platform == "desktop":
            uri_params = {}
            if project_dir:
                uri_params["dir"] = project_dir
            if url:
                uri_params["url"] = url
            uri = f"analytica://desktop/run?{_urlparse.urlencode(uri_params)}"
        elif platform == "web":
            uri = f"analytica://web/open?url={_urlparse.quote(url)}"
        elif platform == "mobile":
            mobile_platform = params.get("mobile_platform", "android")
            uri = f"analytica://mobile/run?platform={mobile_platform}"
            if project_dir:
                uri += f"&dir={_urlparse.quote(project_dir)}"
        else:
            uri = f"analytica://{platform}/run"
    
    launched = False
    message = ""
    
    try:
        result = subprocess.Popen(
            ["xdg-open", uri],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        launched = True
        message = f"Launched: {uri}"
        ctx.log(f"Launch: {uri}")
    except Exception as e:
        message = f"Failed to launch: {e}"
        ctx.log(f"Launch failed: {e}", level="error")
    
    config = {
        "type": "launch",
        "platform": platform,
        "uri": uri,
        "launched": launched,
        "message": message,
    }
    
    if isinstance(data, dict):
        result_data = dict(data)
        result_data["launch"] = config
        return result_data
    
    return {
        "data": data,
        "launch": config,
        "status": "launched" if launched else "failed"
    }


@AtomRegistry.register("deploy", "run")
def deploy_run(ctx, **params) -> Dict:
    """
    Alias for deploy.launch - run deployed application.
    
    Usage:
        deploy.run(platform="desktop", dir="/path/to/project")
        deploy.run("desktop")
    """
    return deploy_launch(ctx, **params)


# ============================================================
# PIPELINE EXPORT ATOMS
# ============================================================

@AtomRegistry.register("deploy", "export_dsl")
def deploy_export_dsl(ctx, **params) -> Dict:
    """
    Export pipeline to DSL file for deployment.
    
    Usage:
        deploy.export_dsl(path="pipelines/main.dsl", format="native")
        deploy.export_dsl(format="json", path="pipelines/main.json")
    """
    data = ctx.get_data()
    path = params.get("path", params.get("_arg0", "pipeline.dsl"))
    fmt = params.get("format", "native")
    
    config = {
        "type": "export",
        "path": path,
        "format": fmt,
        "pipeline": data
    }
    
    ctx.log(f"Export DSL: {path} ({fmt})")
    return _deploy_result(config, {"format": fmt, "path": path})


@AtomRegistry.register("deploy", "bundle")
def deploy_bundle(ctx, **params) -> Dict:
    """
    Bundle DSL pipeline with runtime for standalone deployment.
    
    Usage:
        deploy.bundle(target="standalone", include_runtime=true)
    """
    data = ctx.get_data()
    target = params.get("target", params.get("_arg0", "standalone"))
    include_runtime = params.get("include_runtime", True)
    minify = params.get("minify", True)
    
    config = {
        "type": "bundle",
        "target": target,
        "include_runtime": include_runtime,
        "minify": minify,
        "pipeline": data
    }
    
    ctx.log(f"Bundle: target={target}")
    return _deploy_result(config, {"target": target})
