![](https://raw.githubusercontent.com/rafal-qa/slopo/refs/heads/main/doc/logo.png)

# Slopo

Embedding models are typically used for finding text written differently but having similar meaning. Some models are able to do the same with source code. Slopo is a CLI tool that uses this technology for finding hardest-to-detect code duplicates.

To learn what embeddings can detect, where they are weak, and which models work best, see [Embedding models benchmark for code duplication detection](https://rkochanowski.com/article/embedding-benchmark/). It was written by the author of this tool, so its conclusions apply directly here. The sample configuration in this documentation is the one that performed best in the benchmark.

Slopo helps with:

- Analysis of the whole codebase to find similar code. For refactoring and maintenance.
- Review of recent changes to find similar code between modified or new part and the rest of codebase. For reviewing AI-generated code before committing because AI may re-implement the same solution that already exists somewhere.

### Supported languages

Python, TypeScript, JavaScript, Java, Kotlin, C#, Go, Rust, PHP, Elixir

## How it works

In addition to detecting non-exact code duplication, it focuses on code sitting far apart in the codebase, often spread across different modules or separated within a large file. Exact copy-paste is easy for other tools to spot, and duplicates that are close together are easy for humans or AI to spot.

The result is clusters of similar code, ranked by similarity and by distance in the codebase. These are meant as input for your AI coding agent, which can check whether a cluster is a real duplicate. Reviewed ones can be marked as ignored or passed on for refactoring.

[Example report](doc/example-report) generated from Slopo code (`src` directory, git tag `v0.2.0`).

## Accessing embedding model

According to the benchmark, two providers are recommended:

1. [Jina AI](https://jina.ai/) - code-focused models available via API and for local use
2. [Voyage AI](https://www.voyageai.com/) - only their general-purpose model, their code-focused models are not suitable here

Jina AI offers API keys with free tokens for non-commercial use, without registration. Paid options are available for commercial use. Simply open the main page, and the token will be generated. You should see "_You have 10,000,000 tokens left in the API key below._" However, free tokens are not always granted - this is probably because of abuse prevention mechanisms based on IP address or other measures (it's a guess, not official information).

### Local model

One tested solution is to use [Ollama](https://ollama.com) with `jina-embeddings-v2-base-code`. This is a small model that also runs on a CPU, but it may be (significantly) slower than the API, depending on the hardware you use. Pull the model [from here](https://ollama.com/unclemusclez/jina-embeddings-v2-base-code).

### Other models

Any model provider [supported by LiteLLM](https://docs.litellm.ai/docs/providers) can be configured. Additionally, any OpenAI-compatible server is supported.

## Quick start

Once you figure out the model, the rest is quick.

### Installation

```bash
uv tool install slopo
```

Update to the latest version (there are no automatic updates)

```bash
uv tool upgrade slopo
```

This command uses `uv` ([installing uv](https://docs.astral.sh/uv/getting-started/installation/)), a Python package manager, to install Slopo from [PyPI](https://pypi.org/project/slopo/) in an isolated virtual environment. No need to get Python separately.

### Setup

Run `slopo init` to create a config file template containing further instructions. Only the directory with code for analysis and embedding model configuration is required.

### Model configuration

#### Jina AI

```yaml
embedding_model: jina_ai/jina-code-embeddings-0.5b
embedding_dimensions: 256
embedding_params:
  task: code2code.query
```

If you are embedding a large project with the free API key and hitting rate limits, add the `embedding_request_delay: 6` option to slow down.

#### Voyage AI

```yaml
embedding_model: voyage/voyage-4-large
embedding_dimensions: 256
```

#### Local model

```yaml
embedding_model: ollama/unclemusclez/jina-embeddings-v2-base-code
embedding_dimensions: 768
```

### Running

Run `slopo show-config` to validate your config and show all configurable parameters, most are optional with sensible defaults.

Now you are ready to index code and calculate embeddings:

```bash
slopo index
slopo embed
```

To generate a report, run `slopo analyze` for the whole indexed codebase or `slopo review` for Git changes.

## Getting results

When code changes, run `index` and `embed` to synchronize data before getting a report.

### Analyze the whole project

`slopo analyze` generates a report for code across the whole indexed codebase.

Each cluster has a hash, which can be added to `slopo.ignore.txt` to discard them in analysis. Simply ask your AI coding agent to filter out clusters that are not real duplicates.

### Review recent changes

`slopo review` generates a report for code involving Git changes.

- The default `HEAD` base can be configured with the `--base` option, for example `slopo review --base HEAD~1`
- Untracked files are included as long as they are indexed.
- It targets similar code across changed files and between changed and unchanged parts of the codebase.
- This feature requires `git` installed and `source_dir` must be a Git repository.
- The result can be evaluated by AI coding agent like in `analyze`.

## Configuration

Run `slopo --help` and `slopo show-config` to explore it by yourself anytime.

Most configuration is done with a configuration file with two exceptions:
1. The location of the configuration file can be overridden with the `--config` option.
2. The API key can be set with the `SLOPO_EMBEDDING_API_KEY` environment variable, also picked up from a `.env` file in the current directory.

**Be aware that some parameters can't be changed after first indexing.** You need to remove `slopo.db` and index/embed from the beginning: `source_dir`, `embedding_model`, `embedding_dimensions`, `body_node_count_threshold`.

### All configurable parameters

- `source_dir`: Source directory with code to index, absolute or relative path.
- `source_dir_exclude`: .gitignore-style patterns to exclude from indexing.
- `db_file`: SQLite database file with tool data.
- `report_dir`: Output directory for analysis report.
- `ignore_file`: Text file with ignored clusters.
- `embedding_model`: Embedding model name in LiteLLM format.
- `embedding_dimensions`: Embedding dimensions compatible with the used model. This value is also used to verify received embeddings dimensions.
- `embedding_api_key`: API key for embedding provider, alternatively configured with an environment variable. Optional, no need to set for local models.
- `embedding_params`: Additional properties passed to the LiteLLM and embedding API. Anything supported by the API provider is valid. Example:
```yaml
embedding_params:
  api_base: http://example.com:123
  task: code2code.query
```
- `embedding_batch_size` and `embedding_batch_chars`: Requests to the embedding API are batched for performance. Defaults are fine for most cases.
- `embedding_request_delay`: Delay in seconds after every batched request, by default no delay. Increase if you reach rate limits.
- `similarity_threshold`: Controls minimal cosine similarity between embeddings.
- `rerank_threshold`: Controls minimal similarity after applying a boost reflecting distance in the codebase.
- `body_node_count_threshold`: Number of AST nodes inside the body (excluding signature and annotations). This value reflects the minimum code complexity of the included code unit, more precise than text length. Increase if you notice unwanted, too-small code units in the report.

## Portability

Hashes in a report generated by `analyze` are intended to be stable across platforms and the `slopo.ignore.txt` to be committed to Git and used by the whole team. Note that the hash changes when any code unit in the cluster changes or it's moved.

`slopo.conf.yaml` with `source_dir` relative to the project root can be committed and used across the team.

The order of code units in clusters can differ across platforms, but results should be the same, and the report is not intended to be committed. Embedding models don't return exactly the same floats every time, and this may cause edge cases when results differ a bit.

The tool's database `slopo.db` is local to each developer and not intended to be portable.

## Is it the right tool?

Slopo aims to solve one narrow problem. It focuses on detecting duplicated code that other tools miss: the similar logic implemented in different ways. This has its own trade-offs: the need to use embedding models and producing many false positives that need to be filtered out.

It naturally detects also exact copies and slightly changed clones, which can be detected by other tools. If this is only what you need, those tools are a better fit. They are deterministic, faster, more mature, and don't require the whole ceremony involving embedding models.

## Details

### Ranking thresholds

Similar code units are filtered in two passes, each with its own configurable threshold. The pipeline is as follows:

1. `similarity_threshold` filters out code unit pairs whose embeddings are not similar enough. The calculated value is cosine similarity ranging from `-1` to `1` where `1` means the same.
2. Similar pairs are grouped in clusters.
3. Units in clusters are reranked after applying a boost. Boost is calculated based on the number of directory hops required to reach the other file in the pair (max. 15%). If they are in the same file, the boost is calculated based on distance in number of lines (max. 10%). `rerank_threshold` filters out clusters whose highest-scoring pair is not high enough.

### Exact-copy duplicates

The main goal of this tool is to detect non-exact code duplication, but exact copies (identical code at multiple paths) are reported too, just handled a little differently from merely similar code:

- The report shows the code once, listing every path where it appears, instead of repeating identical snippets.
- The `analyze` command reports the "similarity ratio" (the share of code units flagged as similar) in two variants: including and excluding exact copies.

## Contribution

Pull requests are not accepted and disabled for this repository.

Other contribution types are welcome, especially feedback and human-to-human discussion about ideas, use cases, workflows, friction points.
