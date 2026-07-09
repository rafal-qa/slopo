from slopo.config import Config
from slopo.embedding.models import UnembeddedUnit, EmbeddedUnit


class EmbeddingError(Exception):
    pass


def embed_units(batch: list[UnembeddedUnit], config: Config) -> list[EmbeddedUnit]:
    import litellm  # type: ignore[import-untyped]

    litellm.suppress_debug_info = True
    try:
        response = litellm.embedding(
            model=config.embedding_model,
            input=[u.body for u in batch],
            dimensions=config.embedding_dimensions,
            api_key=config.embedding_api_key,
            api_base=config.embedding_api_base,
        )
    except tuple(litellm.LITELLM_EXCEPTION_TYPES) as e:  # type: ignore[misc]
        raise EmbeddingError(str(e)) from e

    result = []
    for unit, item in zip(batch, response.data):
        vector = item["embedding"]
        if len(vector) != config.embedding_dimensions:
            raise EmbeddingError(
                f"Embedding model '{config.embedding_model}' returned a vector of "
                f"size {len(vector)}, but embedding_dimensions is configured as "
                f"{config.embedding_dimensions}."
            )
        result.append(EmbeddedUnit(body_hash=unit.body_hash, vector=vector))
    return result
