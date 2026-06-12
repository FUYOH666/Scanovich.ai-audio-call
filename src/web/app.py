"""
Minimal FastAPI app for demo uploads and single-file analysis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src import __version__
from src.pipeline_service import CallAnalysisPipeline
from src.utils import ConfigManager, setup_logging

PipelineFactory = Callable[[object], CallAnalysisPipeline]

STATIC_DIR = Path(__file__).with_name("static")
logger = logging.getLogger(__name__)


def create_app(
    config_path: str = "config.yaml",
    pipeline_factory: PipelineFactory | None = None,
) -> FastAPI:
    """Build FastAPI application with shared pipeline lifecycle."""
    pipeline_factory = pipeline_factory or CallAnalysisPipeline

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = ConfigManager(config_path).get()
        setup_logging(config)
        if config.web.require_api_key and not config.web.api_key:
            raise RuntimeError(
                "web.require_api_key=true, but no web.api_key is configured. "
                "Set WEB__API_KEY in the environment or add web.api_key to config.yaml."
            )
        app.state.config = config
        app.state.pipeline = pipeline_factory(config)
        app.state.rate_limit_lock = Lock()
        app.state.rate_limit_buckets = {}
        yield

    app = FastAPI(
        title="Call Analytics Platform API",
        version=__version__,
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/healthz")
    async def healthz(request: Request) -> dict:
        config = request.app.state.config
        pipeline = request.app.state.pipeline

        vllm_available = None
        if config.vllm.enabled:
            vllm_available = await asyncio.to_thread(
                pipeline.vllm_postprocessor.health_check
            )

        return {
            "status": "ok",
            "service": "call-analytics-web",
            "device": config.asr.device,
            "model": config.asr.model,
            "vllm_enabled": config.vllm.enabled,
            "vllm_available": vllm_available,
            "api_key_required": config.web.require_api_key,
        }

    @app.get("/analyses")
    async def list_analyses(
        request: Request,
        limit: int = 20,
        offset: int = 0,
        query: str | None = None,
        has_quality: bool | None = None,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    ) -> dict:
        config = request.app.state.config
        _require_api_key_if_needed(config, x_api_key)

        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)
        items, total_count = _list_recent_analyses(
            config,
            limit=safe_limit,
            offset=safe_offset,
            query=query,
            has_quality=has_quality,
        )
        next_offset = safe_offset + len(items)
        has_more = next_offset < total_count
        return {
            "items": items,
            "count": len(items),
            "total_count": total_count,
            "offset": safe_offset,
            "limit": safe_limit,
            "next_offset": next_offset if has_more else None,
            "has_more": has_more,
        }

    @app.get("/analyses/{result_id}")
    async def get_analysis(
        result_id: str,
        request: Request,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    ) -> dict:
        config = request.app.state.config
        _require_api_key_if_needed(config, x_api_key)
        return _get_analysis_detail(config, result_id)

    @app.post("/analyze")
    async def analyze_audio(
        request: Request,
        file: Annotated[
            UploadFile, File(description="Audio file to analyze")
        ],
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    ) -> dict:
        config = request.app.state.config
        temp_dir: Path | None = None

        try:
            _require_api_key_if_needed(config, x_api_key)
            _enforce_rate_limit(request, config)
            temp_dir, temp_path, safe_name = await _save_upload_to_temp_file(file, config)
            result = await asyncio.to_thread(
                request.app.state.pipeline.analyze_file,
                temp_path,
                safe_name,
                True,
                None,
            )
            return result.to_api_dict()
        except HTTPException:
            raise
        except ValueError as exc:
            logger.warning("Upload rejected or audio invalid: %s", exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            logger.error("Unhandled error during web analysis", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal processing error. Check server logs for details.",
            ) from exc
        finally:
            await file.close()
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    return app


async def _save_upload_to_temp_file(file: UploadFile, config) -> tuple[Path, Path, str]:
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = Path(filename).suffix.lower()
    if extension not in config.security.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {extension or 'none'}",
        )

    max_bytes = config.security.max_file_size_mb * 1024 * 1024
    total_bytes = 0
    temp_dir = Path(tempfile.mkdtemp(prefix="call-analytics-upload-"))
    temp_path = temp_dir / filename

    with temp_path.open("wb") as temp_file:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Uploaded file is too large. "
                        f"Limit: {config.security.max_file_size_mb} MB"
                    ),
                )
            temp_file.write(chunk)

    return temp_dir, temp_path, filename


def _require_api_key_if_needed(config, provided_api_key: str | None) -> None:
    if not config.web.require_api_key:
        return

    if not provided_api_key or provided_api_key != config.web.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _list_recent_analyses(
    config,
    *,
    limit: int,
    offset: int,
    query: str | None,
    has_quality: bool | None,
) -> tuple[list[dict], int]:
    result_ids = _discover_result_ids(config)
    analyses = [_build_analysis_summary(config, result_id) for result_id in result_ids]
    analyses = [item for item in analyses if item is not None]
    analyses = _filter_analyses(analyses, query=query, has_quality=has_quality)
    analyses.sort(key=lambda item: item["_sort_timestamp"], reverse=True)

    total_count = len(analyses)
    trimmed = analyses[offset : offset + limit]
    for item in trimmed:
        item.pop("_sort_timestamp", None)
    return trimmed, total_count


def _get_analysis_detail(config, result_id: str) -> dict:
    safe_result_id = _validate_result_id(result_id)
    paths = _analysis_paths(config, safe_result_id)

    if not any(path.exists() for path in paths.values() if path is not None):
        raise HTTPException(status_code=404, detail="Analysis not found")

    metadata = _load_json(paths["metadata"])
    quality = _load_json(paths["quality"])
    cleaned_text = _load_text(paths["transcript"])
    processed_at, _sort_timestamp = _resolve_processed_at(metadata, paths)

    return {
        "result_id": safe_result_id,
        "filename": (metadata or {}).get("filename") or safe_result_id,
        "processed_at": processed_at,
        "summary": _build_analysis_detail_summary(
            classification=(metadata or {}).get("classification"),
            quality=quality,
            paths=paths,
        ),
        "cleaned_text": cleaned_text,
        "classification": (metadata or {}).get("classification"),
        "asr_metrics": (metadata or {}).get("asr_metrics"),
        "quality": quality,
        "artifacts": {
            "transcript_path": str(paths["transcript"]) if paths["transcript"].exists() else None,
            "metadata_path": str(paths["metadata"]) if paths["metadata"].exists() else None,
            "quality_path": str(paths["quality"]) if paths["quality"].exists() else None,
        },
    }


def _build_analysis_summary(config, result_id: str) -> dict | None:
    paths = _analysis_paths(config, result_id)
    if not any(path.exists() for path in paths.values() if path is not None):
        return None

    metadata = _load_json(paths["metadata"])
    quality = _load_json(paths["quality"])
    transcript = _load_text(paths["transcript"])
    processed_at, sort_timestamp = _resolve_processed_at(metadata, paths)

    return {
        "result_id": result_id,
        "filename": (metadata or {}).get("filename") or result_id,
        "processed_at": processed_at,
        "classification": (metadata or {}).get("classification"),
        "quality_summary": _build_quality_summary(quality),
        "transcript_preview": _build_transcript_preview(transcript),
        "artifacts": {
            "has_transcript": paths["transcript"].exists(),
            "has_metadata": paths["metadata"].exists(),
            "has_quality": paths["quality"].exists(),
        },
        "_sort_timestamp": sort_timestamp,
    }


def _discover_result_ids(config) -> list[str]:
    result_ids: set[str] = set()
    candidates = [
        (Path(config.paths.output), "*.txt"),
        (Path(config.paths.metadata), "*.json"),
    ]
    quality_dir = config.quality_analysis.paths.get("individual")
    if quality_dir:
        candidates.append((Path(quality_dir), "*.json"))

    for directory, pattern in candidates:
        if not directory.exists():
            continue
        for path in directory.glob(pattern):
            if path.is_file():
                result_ids.add(path.stem)

    return sorted(result_ids)


def _analysis_paths(config, result_id: str) -> dict[str, Path]:
    safe_result_id = _validate_result_id(result_id)
    quality_dir = config.quality_analysis.paths.get("individual", "./quality_analysis/individual")
    return {
        "transcript": Path(config.paths.output) / f"{safe_result_id}.txt",
        "metadata": Path(config.paths.metadata) / f"{safe_result_id}.json",
        "quality": Path(quality_dir) / f"{safe_result_id}.json",
    }


def _validate_result_id(result_id: str) -> str:
    safe_result_id = Path(result_id).name
    if not result_id or safe_result_id != result_id or result_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid analysis id")
    return safe_result_id


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not parse saved JSON artifact: %s", path)
        return None


def _load_text(path: Path) -> str | None:
    if not path.exists():
        return None

    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Could not read saved text artifact: %s", path)
        return None


def _resolve_processed_at(metadata: dict | None, paths: dict[str, Path]) -> tuple[str | None, float]:
    processed_at = (metadata or {}).get("processed_at")
    if processed_at:
        try:
            parsed = datetime.strptime(processed_at, "%Y-%m-%d %H:%M:%S")
            return processed_at, parsed.timestamp()
        except ValueError:
            logger.warning("Could not parse processed_at=%s", processed_at)

    existing_paths = [path for path in paths.values() if path.exists()]
    if not existing_paths:
        return None, 0.0

    latest_mtime = max(path.stat().st_mtime for path in existing_paths)
    fallback = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return fallback, latest_mtime


def _build_quality_summary(quality: dict | None) -> dict | None:
    if not quality:
        return None

    return {
        "overall_score": quality.get("overall_score"),
        "strengths_count": len(quality.get("strengths", []) or []),
        "weaknesses_count": len(quality.get("weaknesses", []) or []),
    }


def _build_transcript_preview(transcript: str | None, limit: int = 220) -> str | None:
    if not transcript:
        return None

    normalized = " ".join(transcript.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _filter_analyses(
    analyses: list[dict],
    *,
    query: str | None,
    has_quality: bool | None,
) -> list[dict]:
    normalized_query = (query or "").strip().lower()
    filtered = analyses

    if normalized_query:
        filtered = [
            item for item in filtered if _analysis_matches_query(item, normalized_query)
        ]

    if has_quality is not None:
        filtered = [
            item
            for item in filtered
            if item["artifacts"]["has_quality"] is has_quality
        ]

    return filtered


def _analysis_matches_query(item: dict, query: str) -> bool:
    haystacks = [
        item.get("result_id"),
        item.get("filename"),
        item.get("transcript_preview"),
    ]
    classification = item.get("classification")
    if classification:
        haystacks.append(json.dumps(classification, ensure_ascii=False))

    return any(query in str(value).lower() for value in haystacks if value)


def _build_analysis_detail_summary(
    *,
    classification: dict | None,
    quality: dict | None,
    paths: dict[str, Path],
) -> dict:
    return {
        "classification_type": (classification or {}).get("type"),
        "overall_score": (quality or {}).get("overall_score"),
        "strengths_count": len((quality or {}).get("strengths", []) or []),
        "weaknesses_count": len((quality or {}).get("weaknesses", []) or []),
        "artifacts": {
            "has_transcript": paths["transcript"].exists(),
            "has_metadata": paths["metadata"].exists(),
            "has_quality": paths["quality"].exists(),
        },
    }


def _enforce_rate_limit(request: Request, config) -> None:
    limit_per_hour = config.security.rate_limit_per_hour
    client_id = _request_client_id(request)
    now = time.time()
    window_start = now - 3600

    with request.app.state.rate_limit_lock:
        bucket = request.app.state.rate_limit_buckets.setdefault(client_id, [])
        bucket[:] = [timestamp for timestamp in bucket if timestamp >= window_start]
        if len(bucket) >= limit_per_hour:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Rate limit exceeded for analysis uploads. "
                    "Please wait before sending more files."
                ),
            )
        bucket.append(now)


def _request_client_id(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown-client"


app = create_app()
