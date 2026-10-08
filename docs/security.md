# Security — Media Integrity / SecureCall

## Input Validation

- **MIME/type validation**: All uploaded files are validated against allowed MIME types (image/jpeg, image/png, video/mp4, video/webm, audio/wav, audio/mp3, application/zip)
- **Maximum upload size**: Configurable via `MAX_UPLOAD_MB` (default: 500 MB)
- **Maximum video duration**: Configurable via `MAX_VIDEO_SECONDS` (default: 600 seconds)
- **Maximum ZIP extraction size**: 2× the upload limit to prevent zip bombs
- **File extension validation**: Cross-checked against MIME type
- **Input sanitization**: All user-provided strings sanitized before database storage

## File Storage

- **Randomized storage names**: UUID-based filenames prevent path traversal
- **Path traversal protection**: No user-supplied paths used in file operations
- **Temporary file cleanup**: Automatic cleanup of processing artifacts
- **Configurable retention**: `RETENTION_MODE` controls how long evidence is stored

## Network Security

- **CORS restrictions**: Configurable allowed origins
- **Rate limiting**: Per-IP and per-endpoint rate limits
- **WebSocket authentication**: Session token validation on connection
- **HTTPS**: Required in production (TLS termination at reverse proxy)

## Command Execution

- **No arbitrary command execution**: User input never interpolated into shell commands
- **FFmpeg safety**: Always called via `subprocess` with argument arrays
- **No `shell=True`**: All subprocess calls use explicit argument lists

## Authentication

- Session-based for WebSocket connections
- API key or JWT for REST endpoints (configurable)
- No default passwords

## Logging

- **Never log**: Raw audio, raw video frames, secrets, API keys, passwords
- **Always log**: Request IDs, timestamps, event types, latencies, error codes
- **Structured format**: JSON logging for machine parseability

## Known Attack Surfaces

1. **WebSocket flooding**: Mitigated by rate limiting and bounded queues
2. **Large file upload**: Mitigated by size limits
3. **Malformed media**: Mitigated by FFprobe validation before processing
4. **Path traversal**: Mitigated by UUID storage names
5. **SSRF**: No user-controlled URL fetching implemented
