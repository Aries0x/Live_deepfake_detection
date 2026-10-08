# Licenses — Media Integrity / SecureCall

## Core Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| FastAPI | 0.104+ | MIT | Backend web framework |
| Pydantic | 2.0+ | MIT | Data validation |
| uvicorn | 0.24+ | BSD-3-Clause | ASGI server |
| SQLAlchemy | 2.0+ | MIT | Database ORM |
| Alembic | 1.12+ | MIT | Database migrations |
| asyncpg | 0.29+ | Apache 2.0 | PostgreSQL async driver |
| redis | 5.0+ | MIT | Redis client |
| python-multipart | 0.0.6+ | Apache 2.0 | File upload handling |
| PyTorch | 2.0+ | BSD-3-Clause | ML framework |
| torchvision | 0.15+ | BSD-3-Clause | Image models |
| torchaudio | 2.0+ | BSD-2-Clause | Audio processing |
| OpenCV (cv2) | 4.8+ | Apache 2.0 | Image processing |
| NumPy | 1.24+ | BSD-3-Clause | Numerical computing |
| SciPy | 1.11+ | BSD-3-Clause | Scientific computing |
| librosa | 0.10+ | ISC | Audio feature extraction |
| Pillow | 10.0+ | HPND | Image I/O |
| Next.js | 14+ | MIT | Frontend framework |
| React | 18+ | MIT | UI library |
| Tailwind CSS | 3.0+ | MIT | CSS framework |
| Recharts | 2.0+ | MIT | Charting library |
| Playwright | 1.40+ | Apache 2.0 | Browser testing |
| pytest | 7.0+ | MIT | Python testing |

## ML Models

| Model | Code License | Weight License | Dataset License | Status |
|-------|-------------|----------------|-----------------|--------|
| SCRFD | MIT | LICENSE_REVIEW_REQUIRED | N/A | Review needed for weight redistribution |
| EfficientNet (torchvision) | BSD-3-Clause | BSD-3-Clause (ImageNet pretrained) | ImageNet terms | OK for research |
| AASIST | MIT | MIT | ASVspoof CC BY 4.0 | OK |
| ArcFace | MIT | LICENSE_REVIEW_REQUIRED | MS1M license varies | Review needed |
| SyncNet | BSD-3-Clause | LICENSE_REVIEW_REQUIRED | VoxCeleb terms | Review needed |
| Grad-CAM (pytorch-grad-cam) | MIT | N/A (no weights) | N/A | OK |

## Infrastructure

| Software | License | Purpose |
|----------|---------|---------|
| PostgreSQL | PostgreSQL License (MIT-like) | Database |
| Redis | BSD-3-Clause | Caching/queues |
| FFmpeg | LGPL 2.1 / GPL (depending on build) | Media processing |
| Docker | Apache 2.0 | Containerization |
| Node.js | MIT | JavaScript runtime |

## Notes

- Items marked `LICENSE_REVIEW_REQUIRED` need human review before commercial deployment
- Research/academic use is generally permitted for all listed components
- FFmpeg license depends on compile-time options — use LGPL build for commercial use
- Always check latest license terms as they may change between versions
