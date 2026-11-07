# Data Model: Matched-Core Benchmark

## Thread request and usage

`requested_cpu_threads`: positive integer or null for default; absent in legacy entries also means default. `cpu_threads`: existing positive integer, the configured CPU computation thread count reported at startup. Explicit requests must not exceed process-available CPUs and must match the reported configured count. The count is neither a core-affinity guarantee nor a count of all OS threads.

## Docker allocation observation

`docker_cpus`: existing positive integer or `"unknown"` for Docker; retain existing native representation. A known new observation comes from a host launcher that identifies a running Colima profile and matches its Docker endpoint to the endpoint used for the run. Missing, invalid, unverifiable or mismatched evidence produces unknown. Launcher evidence reflects allocation at launch, not a guarantee against later VM reconfiguration. Legacy values remain readable as historical recorded values, without asserting their provenance.

## Benchmark entry and summary

A successful training run appends one entry using the existing version-1 transactional publication and all existing metrics, plus `requested_cpu_threads`. Failure before validation or publication writes no entry or checkpoint. Older entries remain unchanged and readable.

A row key comprises the existing dataset fingerprint, seed, epochs, batch size, environment and device, plus `cpu_threads` and, for Docker, `docker_cpus` including unknown. Each row has its own run count, measured time averages and paired accuracy. A row can contain explicit and default requests with the same actual count; label that provenance mixed. GPU rows identify the whole GPU and CPU-side thread count. Missing configurations retain the feature 004 marker.
