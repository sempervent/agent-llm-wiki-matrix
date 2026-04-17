// Multi-platform image builds for agent-llm-wiki-matrix orchestration.
// Default: linux/amd64 + linux/arm64. Use variables for single-arch CI or slower machines.
//
// Examples:
//   docker buildx bake
//   docker buildx bake orchestrator --set "*.platform=linux/arm64"
//   PLATFORM=linux/amd64 docker buildx bake orchestrator

variable "TAG" {
  default = "local"
}

variable "REGISTRY" {
  default = ""
}

variable "PLATFORM" {
  default = "linux/amd64,linux/arm64"
}

group "default" {
  targets = ["orchestrator"]
}

// Full multi-arch manifest (default).
target "orchestrator" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "runtime"
  platforms  = [for p in split(",", PLATFORM) : trimspace(p)]
  tags = compact([
    "${REGISTRY}agent-llm-wiki-matrix:${TAG}",
    "agent-llm-wiki-matrix:${TAG}",
  ])
}

// Convenience: single-arch amd64 (faster iteration).
target "orchestrator-amd64" {
  inherits = ["orchestrator"]
  platforms = ["linux/amd64"]
}

// Convenience: single-arch arm64 (Apple Silicon native, ARM servers).
target "orchestrator-arm64" {
  inherits = ["orchestrator"]
  platforms = ["linux/arm64"]
}

// Test image + Playwright Chromium (for optional browser-verify Compose profile).
target "browser-test" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "browser-test"
  platforms  = ["linux/amd64"]
  tags = [
    "agent-llm-wiki-matrix:browser-test",
  ]
}

// Extension point: other ARM variants (e.g. linux/arm/v7) require explicit
// base image support and testing; add new targets here when validated.
