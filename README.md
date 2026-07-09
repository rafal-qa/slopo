![](https://raw.githubusercontent.com/rafal-qa/slopo/refs/heads/main/doc/logo.png)

# Slopo

A CLI tool for detecting non-exact code duplication using embedding models.

It focuses on the similar code that is hardest to detect and most harmful: snippets written similarly, sitting far apart in the codebase, often spread across different modules or separated within a large file. Exact copy-paste is easy to spot by other tools, and duplicates that are close together are easy to spot by humans or AI.

For more high-level description of the problem and example LLM prompts see [slopo.dev](https://slopo.dev/).

### Supported languages

Python, TypeScript, JavaScript, Java, Kotlin, C#, Go, Rust, PHP, Elixir

## How it works

It takes a different approach than typical duplication detection. For every code unit, it calculates an embedding, then looks for pairs whose embeddings are close. Similar code is not necessarily a duplicate, so each pair is a potential duplicate to confirm. Code doing the same thing but implemented in a completely different way produces distant embeddings and won't be detected.

The result is clusters of similar code units, ranked by similarity and by distance in the codebase. These clusters are meant as input for your AI coding agent, which can check whether a cluster is a real duplicate. Reviewed clusters can be marked as ignored or passed on for refactoring.

### Example report

See [doc/example-report](doc/example-report) generated from Slopo code, `src` directory, git tag `v0.2.0`.

This example confirmed that code parsers for each language have a lot of duplication, some are exact-copy, some are similar variants. It needs to be refactored.

## Quick start

### Installation

```bash
uv tool install slopo
```

or upgrade to the latest version

```bash
uv tool upgrade slopo
```

This command uses `uv` ([installing uv](https://docs.astral.sh/uv/getting-started/installation/)), a Python package manager, to install/upgrade Slopo from [PyPI](https://pypi.org/project/slopo/) in an isolated virtual environment. No need to get Python separately.

### Setup

Run `slopo init` to create a config file template containing further instructions. Only the directory with code for analysis and embedding model configuration is required.

### Embedding model

#### Option 1: External provider

Embeddings can be calculated using an external provider. For best results, consider models dedicated to code, e.g. [Voyage AI](https://docs.voyageai.com/docs/embeddings) (it works fine with low dimensions like `512`).

You can use any model provider compatible with LiteLLM, [see details here](https://docs.litellm.ai/docs/embedding/supported_embedding).

The provider API key can be set as an environment variable for better security.

#### Option 2: Local model

Any OpenAI-compatible server with custom `api_base` is supported, see LiteLLM docs.

[Ollama](https://ollama.com) is also supported, and you can use `jina-embeddings-v2-base-code` model without AI-specialized hardware.

1. Install Ollama
2. Pull model [from here](https://ollama.com/unclemusclez/jina-embeddings-v2-base-code)
3. Configure Slopo
    ```yaml
    embedding_model: ollama/unclemusclez/jina-embeddings-v2-base-code
    embedding_dimensions: 768
    embedding_api_base: http://localhost:11434
    ```

### Analysis

Run `slopo show-config` to validate your config and show all configurable parameters, most are optional with sensible defaults.

Now you are ready to index code, calculate embeddings and generate a report:

```bash
slopo index
slopo embed
slopo analyze
```

## Real workflow

This section demonstrates how Slopo can be used in a real development workflow.

It utilizes incremental re-indexing (update index with changed files only) and `slopo.ignore.txt` to discard already reviewed clusters.

1. Create your first analysis and check results. You will notice `index.md` containing a list of all clusters and cluster details per file.
2. You may want to exclude some directories or file patterns, usually excluding tests is a good idea. You can also tune thresholds if the result is too big or too small.
3. Once satisfied with analysis results, ask your AI coding agent to filter out clusters that are not real duplicates. This is a common case because not every similar code is a duplication to act on. Ask the AI agent to add discarded cluster hashes to `slopo.ignore.txt`.
4. Re-run the analysis to generate a report without reviewed clusters. This is a basis for refactoring, which can be done by an AI agent.
5. `ignore` file can be committed to your Git repository and reused cross-team. New and modified clusters will reappear in the report. A configuration file without an API key can also be committed. Don't commit `slopo.db`, this is your local data.

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
- `embedding_api_base`: HTTP base URL for embedding service.
- `embedding_batch_size` and `embedding_batch_chars`: Requests to the embedding API are batched for performance. Defaults are fine for most cases.
- `similarity_threshold`: Controls minimal cosine similarity between embeddings.
- `rerank_threshold`: Controls minimal similarity after applying a boost reflecting distance in the codebase.
- `body_node_count_threshold`: Number of AST nodes inside the body (excluding signature and annotations). This value reflects the minimum code complexity of the included code unit, more precise than text length. Increase if you notice unwanted, too-small code units in the report.

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
