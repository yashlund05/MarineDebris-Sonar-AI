"""Empirical Adversarial Test Suite for Milestone 1 Adapters.

Target: RTSPStreamAdapter, ReplayStreamAdapter, NativeSonarStubAdapter.
Author: teamwork_preview_challenger_m1_2
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile
import pytest

from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import (
    RTSPStreamAdapter,
    sanitize_rtsp_uri,
    validate_rtsp_uri,
)
from backend.live_sonar.models import (
    LiveSonarSecurityViolationError,
    LiveSonarSessionConfig,
    LiveSonarSourceConnectionError,
    LiveSonarSourceInvalidError,
    SessionStatus,
)
from backend.live_sonar.session import LiveSonarSession


# ==============================================================================
# 1. RTSP ADAPTER ADVERSARIAL CHALLENGES (SSRF, Credentials, Injections)
# ==============================================================================

class TestRTSPAdversarialSecurity:
    """Adversarial stress-testing of RTSPStreamAdapter and validate_rtsp_uri."""

    def test_rtsp_ssrf_direct_metadata(self):
        """Direct 169.254.169.254 metadata endpoint must be blocked."""
        with pytest.raises(LiveSonarSecurityViolationError, match="169.254.169.254"):
            validate_rtsp_uri("rtsp://169.254.169.254/secret")

        with pytest.raises(LiveSonarSecurityViolationError, match="169.254.169.254"):
            validate_rtsp_uri("rtsp://169.254.169.254:554/feed")

    def test_rtsp_ssrf_link_local_subnet_gap(self):
        """Link-local 169.254.0.0/16 subnet must be blocked."""
        with pytest.raises(LiveSonarSecurityViolationError):
            validate_rtsp_uri("rtsp://169.254.1.1/secret")

    def test_rtsp_ssrf_ipv6_mapped_gap(self):
        """IPv6 mapped representation [::ffff:169.254.169.254] must be blocked."""
        with pytest.raises(LiveSonarSecurityViolationError):
            validate_rtsp_uri("rtsp://[::ffff:169.254.169.254]/secret")

    def test_rtsp_network_allowlist_enforcement_gap(self):
        """When network_allowlist is configured, hosts NOT in allowlist must be blocked."""
        with pytest.raises(LiveSonarSecurityViolationError):
            validate_rtsp_uri(
                "rtsp://192.168.1.100:554/feed",
                network_allowlist=["10.0.0.1", "10.0.0.2"],
            )
        # And allowed hosts must pass without error
        validate_rtsp_uri(
            "rtsp://192.168.1.100:554/feed",
            network_allowlist=["192.168.1.0/24"],
        )

    def test_rtsp_scheme_tampering(self):
        """Non-RTSP protocols must be rejected."""
        disallowed_schemes = [
            "http://192.168.1.1:80/stream",
            "https://192.168.1.1:443/stream",
            "ftp://192.168.1.1/stream",
            "file:///etc/passwd",
            "gopher://127.0.0.1:6379/",
            "ws://192.168.1.1:8080/live",
            "javascript:alert(1)",
        ]
        for uri in disallowed_schemes:
            with pytest.raises(LiveSonarSecurityViolationError, match="Invalid RTSP protocol scheme"):
                validate_rtsp_uri(uri)

    def test_rtsp_missing_or_empty_hostname(self):
        """URIs with missing or invalid hostnames must be rejected."""
        invalid_uris = [
            "rtsp:///path/to/stream",
            "rtsp://:554/path",
            "rtsp://",
        ]
        for uri in invalid_uris:
            with pytest.raises(LiveSonarSourceInvalidError):
                validate_rtsp_uri(uri)

    def test_rtsp_loopback_restriction(self):
        """Loopback addresses must be blocked when allow_local=False."""
        loopback_uris = [
            "rtsp://localhost:554/live",
            "rtsp://127.0.0.1:554/live",
            "rtsp://[::1]:554/live",
        ]
        for uri in loopback_uris:
            with pytest.raises(LiveSonarSecurityViolationError, match="loopback"):
                validate_rtsp_uri(uri, allow_local=False)

    def test_rtsp_credential_sanitization_robustness(self):
        """Verify credential sanitization across various complex password formats."""
        test_cases = [
            (
                "rtsp://admin:hunter2@192.168.1.100:554/live",
                "rtsp://***:***@192.168.1.100:554/live",
            ),
            (
                "rtsp://user:p%40ssw0rd!@10.0.0.5:8554/sonar",
                "rtsp://***:***@10.0.0.5:8554/sonar",
            ),
            (
                "rtsp://admin:@192.168.1.1:554/stream",
                "rtsp://***:***@192.168.1.1:554/stream",
            ),
            (
                "rtsp://:password123@192.168.1.1:554/stream",
                "rtsp://***:***@192.168.1.1:554/stream",
            ),
            (
                "rtsp://192.168.1.100:554/live?token=secret123",
                "rtsp://192.168.1.100:554/live?token=***",
            ),
            (
                "rtsp://admin:hunter2@192.168.1.100:554/live?key=superkey&fps=15",
                "rtsp://***:***@192.168.1.100:554/live?key=***&fps=15",
            ),
        ]
        for raw, expected in test_cases:
            sanitized = sanitize_rtsp_uri(raw)
            assert sanitized == expected, f"Failed for {raw}: got {sanitized}"
            assert "hunter2" not in sanitized
            assert "password123" not in sanitized
            assert "secret123" not in sanitized
            assert "superkey" not in sanitized

    @pytest.mark.asyncio
    async def test_rtsp_credential_non_leakage_in_failure(self):
        """Verify credentials do not leak into health, metadata, or exception messages."""
        secret_pass = "SuperSecretPassword999!"
        raw_uri = f"rtsp://admin:{secret_pass}@192.0.2.1:554/stream"
        adapter = RTSPStreamAdapter(
            source_uri=raw_uri,
            max_reconnect_attempts=1,
            connect_timeout_sec=1.0,
        )

        with pytest.raises(LiveSonarSourceConnectionError) as exc_info:
            await adapter.connect()

        # Check exception message
        assert secret_pass not in str(exc_info.value)
        assert "admin" not in str(exc_info.value)

        # Check health report
        health = await adapter.health()
        assert secret_pass not in health.details
        assert secret_pass not in health.source_uri

        # Check metadata
        meta = await adapter.metadata()
        assert secret_pass not in meta.source_uri

    def test_rtsp_command_injection_characters_not_crashing_parser(self):
        """Verify URI parser handles shell metacharacters safely without crashing."""
        injected_uris = [
            "rtsp://192.168.1.1/stream; echo PWNED",
            "rtsp://192.168.1.1/stream && cat /etc/passwd",
            "rtsp://192.168.1.1/stream | whoami",
            "rtsp://192.168.1.1/stream`id`",
            "rtsp://192.168.1.1/stream$(touch /tmp/pwn)",
        ]
        for uri in injected_uris:
            # Should parse without unexpected unhandled Python runtime crashes
            validate_rtsp_uri(uri)
            sanitized = sanitize_rtsp_uri(uri)
            assert isinstance(sanitized, str)


# ==============================================================================
# 2. REPLAY ADAPTER ADVERSARIAL CHALLENGES (Path Traversal, Non-existent Files)
# ==============================================================================

class TestReplayAdversarialResilience:
    """Adversarial stress-testing of ReplayStreamAdapter."""

    @pytest.mark.asyncio
    async def test_replay_relative_path_traversal_blocked(self):
        """Relative path traversals attempting to escape cwd must be blocked."""
        traversal_attempts = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "data/../../secret.txt",
            "./data/../../windows",
        ]
        for path in traversal_attempts:
            adapter = ReplayStreamAdapter(source_uri=path)
            with pytest.raises(LiveSonarSourceInvalidError, match="Path traversal"):
                await adapter.connect()

    @pytest.mark.asyncio
    async def test_replay_absolute_path_traversal_gap(self):
        """Demonstrate that absolute paths containing '..' bypass the traversal guard."""
        # Because replay.py line 107 checks: 'if ".." in self.source_uri and not os.path.isabs(self.source_uri):'
        # An absolute path containing '..' completely bypasses the path traversal check!
        abs_traversal_path = str(Path.cwd().resolve() / ".." / ".." / "nonexistent_sentinel_xyz.png")
        adapter = ReplayStreamAdapter(source_uri=abs_traversal_path)
        # It bypasses the 'Path traversal detected' check and instead fails on 'does not exist'
        with pytest.raises(LiveSonarSourceInvalidError) as exc_info:
            await adapter.connect()
        assert "Path traversal detected" not in str(exc_info.value), (
            "Empirical finding: Absolute path containing '..' bypassed traversal check"
        )

    @pytest.mark.asyncio
    async def test_replay_unrestricted_filesystem_access(self, tmp_path):
        """Demonstrate ReplayStreamAdapter can load arbitrary files anywhere on host filesystem."""
        # Create an external directory outside repo
        ext_img = tmp_path / "external_outside_repo.png"
        import cv2
        import numpy as np
        cv2.imwrite(str(ext_img), np.zeros((32, 32), dtype=np.uint8))

        adapter = ReplayStreamAdapter(source_uri=str(ext_img))
        await adapter.connect()
        assert adapter.is_connected
        assert adapter._mode == "image_sequence"
        assert adapter._total_frames == 1
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_replay_empty_and_whitespace_uris_unhandled_os_error(self):
        """Empty or whitespace-only URIs result in unhandled FileNotFoundError on Windows."""
        for uri in ["", "   ", "\t\n"]:
            adapter = ReplayStreamAdapter(source_uri=uri)
            # ReplayStreamAdapter raises raw FileNotFoundError or LiveSonarSourceInvalidError
            with pytest.raises((LiveSonarSourceInvalidError, FileNotFoundError)):
                await adapter.connect()

    @pytest.mark.asyncio
    async def test_replay_directory_with_no_images(self, tmp_path):
        """Directory without supported sonar images must raise LiveSonarSourceInvalidError."""
        empty_dir = tmp_path / "empty_sonar_dir"
        empty_dir.mkdir()

        # Add an unsupported file
        (empty_dir / "readme.txt").write_text("not an image")
        (empty_dir / "data.csv").write_text("1,2,3")

        adapter = ReplayStreamAdapter(source_uri=str(empty_dir))
        with pytest.raises(LiveSonarSourceInvalidError, match="contains no supported sonar image files"):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_replay_unsupported_file_extension(self, tmp_path):
        """File with unsupported extension must raise LiveSonarSourceInvalidError."""
        dummy_file = tmp_path / "payload.py"
        dummy_file.write_text("print('hello')")

        adapter = ReplayStreamAdapter(source_uri=str(dummy_file))
        with pytest.raises(LiveSonarSourceInvalidError, match="Unsupported replay file format"):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_replay_corrupted_image_file_handling(self, tmp_path):
        """A directory containing a 0-byte or corrupted image should be handled gracefully."""
        corrupt_dir = tmp_path / "corrupt_sonar_dir"
        corrupt_dir.mkdir()
        # Create a corrupt 0-byte png
        corrupt_file = corrupt_dir / "corrupt_frame_001.png"
        corrupt_file.write_bytes(b"")

        adapter = ReplayStreamAdapter(source_uri=str(corrupt_dir))
        await adapter.connect()
        assert adapter.is_connected

        # Consuming frames should skip corrupt frame without unhandled crash
        frames = []
        async for f in adapter.frames():
            frames.append(f)
        assert len(frames) == 0
        await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_replay_malformed_manifest_sidecar(self, tmp_path):
        """A directory containing a malformed manifest.json should not crash the adapter."""
        manifest_dir = tmp_path / "manifest_test_dir"
        manifest_dir.mkdir()
        
        real_img = Path("data/test_sonar_images/marine-debris-aris3k-64.png")
        if real_img.exists():
            (manifest_dir / "marine-debris-aris3k-64.png").write_bytes(real_img.read_bytes())
        else:
            pytest.skip("data/test_sonar_images/marine-debris-aris3k-64.png not found")

        # Write invalid JSON into manifest.json
        (manifest_dir / "manifest.json").write_text("{malformed: json, missing quotes}")

        adapter = ReplayStreamAdapter(source_uri=str(manifest_dir))
        await adapter.connect()
        assert adapter.is_connected
        # Manifest metadata should fallback to empty dict
        assert adapter._manifest_metadata == {}

        frames = []
        async for f in adapter.frames():
            frames.append(f)
            break
        assert len(frames) == 1
        await adapter.disconnect()


# ==============================================================================
# 3. NATIVE SONAR STUB ADAPTER ADVERSARIAL CHALLENGES
# ==============================================================================

class TestNativeSonarStubAdversarial:
    """Stress-testing NativeSonarStubAdapter when hardware is absent."""

    @pytest.mark.asyncio
    async def test_native_adapter_hardware_absent_contract(self):
        """Verify strict adherence to NOT_CONFIGURED status contract."""
        adapter = NativeSonarStubAdapter(source_uri="native://aris3000")

        # Must not claim connected before connect()
        assert not adapter.is_connected

        # connect() must fail cleanly with LiveSonarSourceConnectionError
        with pytest.raises(LiveSonarSourceConnectionError) as exc_info:
            await adapter.connect()
        
        err = exc_info.value
        assert "NOT_CONFIGURED" in str(err)
        assert err.error_code == "NATIVE_SONAR_UNAVAILABLE"
        assert err.details.get("status") == "NOT_CONFIGURED"

        # After failure, is_connected must remain False
        assert not adapter.is_connected

        # health() must report NOT_CONFIGURED without raising
        health = await adapter.health()
        assert health.status == "NOT_CONFIGURED"
        assert "NOT_CONFIGURED" in health.details or "not configured" in health.details.lower()

        # metadata() must report NOT_CONFIGURED
        meta = await adapter.metadata()
        assert meta.source_type == "native_stub"
        assert meta.extra.get("status") == "NOT_CONFIGURED"
        assert meta.extra.get("driver_linked") is False

        # frames() must yield nothing and not hang/crash
        frames = []
        async for f in adapter.frames():
            frames.append(f)
        assert len(frames) == 0

        # disconnect() must be idempotent and safe
        await adapter.disconnect()
        assert not adapter.is_connected

    @pytest.mark.asyncio
    async def test_native_adapter_in_live_sonar_session(self):
        """Verify LiveSonarSession properly transitions to ERROR when native hardware absent."""
        config = LiveSonarSessionConfig(
            session_id="session-native-test",
            source_type="native_stub",
            source_uri="native://aris3000",
            target_fps=15.0,
        )
        session = LiveSonarSession(config=config)
        assert session.status == SessionStatus.CONNECTING

        # Starting session with unconfigured hardware must raise LiveSonarSourceConnectionError
        with pytest.raises(LiveSonarSourceConnectionError):
            await session.start()

        # Session status must be ERROR
        assert session.status == SessionStatus.ERROR
        assert session.error_message is not None
        assert "NOT_CONFIGURED" in session.error_message

        # Clean shutdown after error
        await session.stop()
        assert session.status == SessionStatus.STOPPED
