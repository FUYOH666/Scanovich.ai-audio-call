import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from src.pipeline_service import AnalysisResult
from src.web.app import create_app


class FakeVLLMPostprocessor:
    def health_check(self) -> bool:
        return True


class FakePipeline:
    def __init__(self, config):
        self.config = config
        self.calls = []
        self.vllm_postprocessor = FakeVLLMPostprocessor()

    def analyze_file(
        self,
        file_path,
        display_name=None,
        persist=False,
        analyze_quality=None,
    ) -> AnalysisResult:
        file_path_obj = Path(file_path)
        self.calls.append(
            {
                "path": str(file_path_obj),
                "display_name": display_name,
                "persist": persist,
                "analyze_quality": analyze_quality,
                "exists": file_path_obj.exists(),
            }
        )
        return AnalysisResult(
            source_name=display_name or file_path_obj.name,
            raw_transcription="raw text",
            cleaned_text="cleaned text",
            classification={"type": "консультация", "sentiment": "нейтральный"},
            asr_metrics={"elapsed_time": 1.25, "rtf": 0.12},
            quality_result={"overall_score": 88.0},
        )


class ErrorPipeline(FakePipeline):
    def analyze_file(self, *_args, **_kwargs) -> AnalysisResult:
        raise RuntimeError("super secret internal failure")


def write_test_config(
    tmp_path,
    *,
    max_file_size_mb=5,
    rate_limit_per_hour=1000,
    require_api_key=False,
    api_key="",
):
    config_path = tmp_path / "config.yaml"
    logs_path = tmp_path / "logs"
    config = {
        "asr": {
            "model": "tiny",
            "device": "cpu",
            "compute_type": "int8",
        },
        "vllm": {
            "enabled": False,
        },
        "paths": {
            "input": str(tmp_path / "input"),
            "output": str(tmp_path / "output"),
            "metadata": str(tmp_path / "metadata"),
            "archive": str(tmp_path / "archive"),
            "logs": str(logs_path),
        },
        "logging": {
            "files": {
                "main": str(logs_path / "main.log"),
                "errors": str(logs_path / "errors.log"),
            }
        },
        "security": {
            "allowed_extensions": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
            "max_file_size_mb": max_file_size_mb,
            "rate_limit_per_hour": rate_limit_per_hour,
        },
        "web": {
            "host": "127.0.0.1",
            "port": 8080,
            "require_api_key": require_api_key,
            "api_key": api_key,
        },
        "quality_analysis": {
            "enabled": False,
            "paths": {
                "individual": str(tmp_path / "quality_analysis" / "individual"),
                "aggregated": str(tmp_path / "quality_analysis" / "aggregated"),
                "reports": str(tmp_path / "quality_analysis" / "reports"),
            },
        },
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def seed_saved_analysis(
    tmp_path,
    result_id,
    *,
    filename=None,
    processed_at="2026-03-22 10:00:00",
    transcript="saved transcript",
    classification=None,
    asr_metrics=None,
    quality=None,
):
    output_dir = tmp_path / "output"
    metadata_dir = tmp_path / "metadata"
    quality_dir = tmp_path / "quality_analysis" / "individual"

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    quality_dir.mkdir(parents=True, exist_ok=True)

    if transcript is not None:
        (output_dir / f"{result_id}.txt").write_text(transcript, encoding="utf-8")

    if classification is not False:
        metadata_payload = {
            "filename": filename or f"{result_id}.mp3",
            "processed_at": processed_at,
            "classification": classification or {"type": "saved-call"},
            "asr_metrics": asr_metrics or {"elapsed_time": 2.5, "rtf": 0.2},
        }
        (metadata_dir / f"{result_id}.json").write_text(
            json.dumps(metadata_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if quality is not None:
        (quality_dir / f"{result_id}.json").write_text(
            json.dumps(quality, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def test_healthz_returns_ok(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["device"] == "cpu"
    assert response.json()["vllm_enabled"] is False


def test_analyze_returns_expected_payload(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"] == "call.mp3"
        assert payload["cleaned_text"] == "cleaned text"
        assert payload["classification"]["type"] == "консультация"
        assert payload["quality"]["overall_score"] == 88.0
        assert client.app.state.pipeline.calls[0]["persist"] is True
        assert client.app.state.pipeline.calls[0]["exists"] is True


def test_analyze_rejects_unsupported_extension(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"file": ("call.txt", b"not audio", "text/plain")},
        )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_analyze_rejects_large_file(tmp_path):
    config_path = write_test_config(tmp_path, max_file_size_mb=1)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    oversized_payload = b"x" * (1024 * 1024 + 1)

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"file": ("big.mp3", oversized_payload, "audio/mpeg")},
        )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_analyze_requires_api_key_when_enabled(tmp_path):
    config_path = write_test_config(
        tmp_path,
        require_api_key=True,
        api_key="pilot-secret",
    )
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        denied = client.post(
            "/analyze",
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )
        allowed = client.post(
            "/analyze",
            headers={"X-API-Key": "pilot-secret"},
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )

    assert denied.status_code == 401
    assert "API key" in denied.json()["detail"]
    assert allowed.status_code == 200


def test_analyze_hides_internal_error_details(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=ErrorPipeline)

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal processing error. Check server logs for details."


def test_analyze_rate_limits_uploads(tmp_path):
    config_path = write_test_config(tmp_path, rate_limit_per_hour=1)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        first = client.post(
            "/analyze",
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )
        second = client.post(
            "/analyze",
            files={"file": ("call.mp3", b"fake audio bytes", "audio/mpeg")},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.json()["detail"]


def test_analyses_lists_recent_saved_artifacts(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    seed_saved_analysis(
        tmp_path,
        "older-call",
        processed_at="2026-03-22 09:00:00",
        transcript="older transcript",
        quality={"overall_score": 71.0, "strengths": ["a"], "weaknesses": ["b", "c"]},
    )
    seed_saved_analysis(
        tmp_path,
        "newer-call",
        processed_at="2026-03-22 11:00:00",
        transcript="newer transcript",
        quality={"overall_score": 93.0, "strengths": ["a", "b"], "weaknesses": []},
    )

    with TestClient(app) as client:
        response = client.get("/analyses")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["total_count"] == 2
    assert [item["result_id"] for item in payload["items"]] == ["newer-call", "older-call"]
    assert payload["items"][0]["quality_summary"]["overall_score"] == 93.0
    assert payload["items"][0]["artifacts"] == {
        "has_transcript": True,
        "has_metadata": True,
        "has_quality": True,
    }


def test_analyses_lists_orphan_transcript_without_metadata(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    seed_saved_analysis(
        tmp_path,
        "transcript-only",
        transcript="only transcript on disk",
        classification=False,
        quality=None,
    )

    with TestClient(app) as client:
        response = client.get("/analyses")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["result_id"] == "transcript-only"
    assert item["artifacts"]["has_transcript"] is True
    assert item["artifacts"]["has_metadata"] is False
    assert item["artifacts"]["has_quality"] is False


def test_analyses_support_query_filter_and_pagination(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    seed_saved_analysis(
        tmp_path,
        "sales-call",
        filename="sales.mp3",
        transcript="important sales transcript",
        quality={"overall_score": 91.0, "strengths": [], "weaknesses": []},
    )
    seed_saved_analysis(
        tmp_path,
        "support-call",
        filename="support.mp3",
        transcript="support transcript",
        quality=None,
    )
    seed_saved_analysis(
        tmp_path,
        "third-call",
        filename="archive.mp3",
        transcript="older transcript",
        quality={"overall_score": 70.0, "strengths": [], "weaknesses": []},
    )

    with TestClient(app) as client:
        filtered = client.get("/analyses", params={"query": "sales", "has_quality": "true"})
        paged = client.get("/analyses", params={"limit": 1, "offset": 1})

    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload["total_count"] == 1
    assert filtered_payload["items"][0]["result_id"] == "sales-call"

    assert paged.status_code == 200
    paged_payload = paged.json()
    assert paged_payload["count"] == 1
    assert paged_payload["has_more"] is True
    assert paged_payload["next_offset"] == 2


def test_analysis_detail_returns_saved_artifacts(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    seed_saved_analysis(
        tmp_path,
        "saved-call",
        filename="pilot-call.mp3",
        transcript="hello from history",
        classification={"type": "consultation", "sentiment": "positive"},
        asr_metrics={"elapsed_time": 3.7, "rtf": 0.11},
        quality={"overall_score": 86.0, "strengths": ["clarity"], "weaknesses": ["upsell"]},
    )

    with TestClient(app) as client:
        response = client.get("/analyses/saved-call")

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_id"] == "saved-call"
    assert payload["filename"] == "pilot-call.mp3"
    assert payload["cleaned_text"] == "hello from history"
    assert payload["summary"]["classification_type"] == "consultation"
    assert payload["classification"]["type"] == "consultation"
    assert payload["quality"]["overall_score"] == 86.0
    assert payload["artifacts"]["transcript_path"].endswith("saved-call.txt")


def test_analysis_detail_returns_404_when_missing(tmp_path):
    config_path = write_test_config(tmp_path)
    app = create_app(str(config_path), pipeline_factory=FakePipeline)

    with TestClient(app) as client:
        response = client.get("/analyses/missing-call")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_analyses_require_api_key_when_enabled(tmp_path):
    config_path = write_test_config(
        tmp_path,
        require_api_key=True,
        api_key="pilot-secret",
    )
    app = create_app(str(config_path), pipeline_factory=FakePipeline)
    seed_saved_analysis(tmp_path, "saved-call")

    with TestClient(app) as client:
        denied = client.get("/analyses")
        allowed = client.get("/analyses", headers={"X-API-Key": "pilot-secret"})

    assert denied.status_code == 401
    assert allowed.status_code == 200
