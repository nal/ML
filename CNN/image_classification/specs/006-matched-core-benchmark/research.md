# Research: Matched-Core Benchmark

## CPU thread control

**Decision**: Validate the requested positive count against the existing affinity/cgroup-aware availability before loading data or initiating publication recovery. Configure PyTorch intra-operation threads before eager, JIT or autograd work and record `torch.get_num_threads()`; keep all-core default. Inventory the CPU computation pools used by this pipeline and configure any additional active pool before initialization, or demonstrate it is inactive/serial. DataLoader currently uses zero workers. Handle the separate inter-operation pool according to its one-time initialization restriction and test repeated in-process calls; do not claim a process-wide OS thread cap.

**Rationale**: [PyTorch's setter](https://docs.pytorch.org/docs/stable/generated/torch.set_num_threads.html) controls CPU intra-op parallelism and requires early configuration. [Inter-op threads](https://docs.pytorch.org/docs/stable/generated/torch.set_num_interop_threads.html) are a separate, one-time setting. [OpenMP/MKL environment settings](https://docs.pytorch.org/docs/stable/threading_environment_variables.html) can affect additional pools. The configured count is not a measurement of instantaneous active threads or core affinity.

**Alternatives considered**: Count all process threads (includes unrelated background threads); set only PyTorch intra-op while assuming all external pools are covered (unverified).

## VM allocation evidence

**Decision**: Use a host launcher for the documented Colima workflow. Query machine-readable Colima status for a running selected profile and its CPU allocation and Docker socket; match that socket against the Docker endpoint actually used, and only then forward the count and source to the container. Fail closed to unknown when unsupported, ambiguous, stale, malformed, or mismatched; verify behavior using mocked status/context and real Colima acceptance. Existing direct Docker commands remain usable, with unknown VM allocation when no trustworthy observation is available. Do not mount Docker sockets or change VM configuration from the app.

**Rationale**: Container CPU limits and visible CPUs do not establish the VM allocation. [Colima status implementation](https://github.com/abiosoft/colima/blob/main/app/app.go) exposes CPU and Docker socket in JSON; availability must be checked for the installed version. A launcher observation is valid only for the selected endpoint at launch; reconfiguration or context changes during a run are outside the sequential benchmark workflow and must be documented.

**Alternatives considered**: Infer from `os.cpu_count()` (not reliable); accept a bare user-supplied number as verified (does not establish provenance); require privileged host access inside the container (unnecessary).

## Results compatibility and grouping

**Decision**: Extend existing version-1 entries with nullable `requested_cpu_threads`; retain `cpu_threads` and `docker_cpus`. Missing requested field means default. Validate the new field when present without rewriting old entries. Group by existing workload and environment/device keys plus actual CPU threads and Docker VM count, including unknown as a distinct value, and by Docker allocation provenance (launcher, unknown, or legacy-unverified); indicate explicit/default/mixed request provenance in a group. Display MPS as whole GPU with CPU threads separate and use the existing measured averages only.

**Rationale**: Existing validators accept additional fields and old entries already contain actual threads and a historical Docker allocation; separating unverified historical counts from launcher observations prevents implying equal provenance.

**Alternatives considered**: Rewrite old entries or introduce a new format version (unnecessary); group by request alone (can mix different actual resources).
