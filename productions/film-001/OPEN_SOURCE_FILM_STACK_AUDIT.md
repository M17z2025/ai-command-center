# Sigma Film Engine — Open-Source & Infrastructure Audit
Date: 2026-09-27
Mission: PROVE YOU'RE HUMAN / reusable AI movie production engine

## Executive conclusion

The software stack is viable without relying on per-clip paid video generators.

The existing Mi7z/Alysha repositories already contain:
- an AI movie stack manifest;
- a RunPod GPU worker architecture;
- an OVH VPS control-plane architecture;
- RunPod proof worker code;
- a non-deploying RunPod connectivity workflow.

However, this architecture has not been fully commissioned into a working film-rendering service. The current Sigma hardware audit is queued on a self-hosted runner and has not started, so live GPU presence on the OVH host is not yet evidenced.

The correct production architecture is:
- OVH VPS = always-on control plane / queue / orchestration / asset tracking;
- GPU worker = elastic rendering plane;
- R2/Supabase = persistent assets and metadata;
- GitHub = code, workflows, manifests, evidence;
- ComfyUI/FFmpeg = production orchestration and final assembly.

## Existing user-owned GitHub assets

### M17z2025/alisha-os/config/ai-movie-stack.json
Already defines:
- ComfyUI
- LTX-Video
- Wan
- AnimateDiff
- Kokoro
- Chatterbox
- faster-whisper
- Blender
- Real-ESRGAN
- FFmpeg
- RunPod GPU deployment model

Status: design/config only; not evidence of a live production renderer.

### M17z2025/alisha-ai-platform/infra/runtime-placement.json
Already defines:
- OVH VPS as always-on control plane
- RunPod as elastic GPU worker plane
- ComfyUI, LTX, Wan, Whisper, Kokoro, Blender, Real-ESRGAN etc. on RunPod
- explicit guardrail preventing automatic billable GPU activation from merge

### RunPod proof worker
M17z2025/alisha-ai-platform/runpod/proof/handler.py
Provides health/echo proof and reports whether a GPU is visible.

### RunPod endpoint path
The existing infrastructure workflow references a configured RunPod endpoint and a GitHub Actions secret for the RunPod API key, but the connectivity workflow has no verified execution evidence in the currently inspected workflow history.

## Current open-source model findings

### 1. Wan2.2 — primary high-quality video model
Repository: https://github.com/Wan-Video/Wan2.2
License: Apache-2.0 repository.
Relevant model: Wan2.2-TI2V-5B
Official requirements:
- 720p / 24fps
- text-to-video + image-to-video
- >=24GB VRAM for TI2V-5B
- official README reports ~5 seconds of 720p video in under 9 minutes on a consumer-grade GPU without special optimisation
Recommendation: primary hero-shot generator on 24GB+ GPU.

### 2. FramePack — primary long-form / low-VRAM experiment
Repository: https://github.com/lllyasviel/FramePack
Code license: Apache-2.0
Official README:
- supports long next-frame-section video generation
- minimum stated GPU memory 6GB
- demonstrates 1-minute / 30fps generation with 13B model
- 4090 example speed around 1.5–2.5 seconds per generated frame depending on optimisation
Important: underlying model/checkpoint licences must be separately checked.
Recommendation: highest-value route to test for longer continuity with modest VRAM.

### 3. SkyReels V2/V3 — long-form film research path
Repositories:
- https://github.com/SkyworkAI/SkyReels-V2
- https://github.com/SkyworkAI/SkyReels-V3
SkyReels V2:
- explicitly targets infinite-length film generation;
- 1.3B 540p path reports ~14.7GB peak VRAM;
- 14B paths require ~43–51GB peak VRAM.
License is a Skywork community license rather than a standard OSI licence; repository states commercial use is supported subject to its terms.
Recommendation: secondary long-form candidate, especially 1.3B path, after legal licence review.

### 4. DecMem — research-grade minute consistency
Repository: https://github.com/KlingAIResearch/DecMem
License: Apache-2.0 code
Requirements:
- >=24GB VRAM for dense path
- full long-term-memory sparse attention requires H100/H200/H800-class hardware
Recommendation: do not use as baseline; retain as future research path.

### 5. LTX-2.x / LTX-2.5 — technically strong but licence-sensitive
Repository: https://github.com/Lightricks/LTX-2
Current 2026 licence:
- community licence, not Apache;
- entities with >= USD 10m annual revenue need a paid commercial licence for commercial use;
- output rights otherwise remain with the user subject to restrictions.
Recommendation: do not make LTX the default production dependency until the relevant legal/entity threshold is confirmed.

### 6. ComfyUI — orchestration layer
Repository: https://github.com/Comfy-Org/ComfyUI
License: GPL-3.0
Current README states:
- NVIDIA/AMD/Intel/Apple support;
- asynchronous weight streaming;
- can run very large models with low VRAM at reduced performance.
Recommendation: standard workflow engine.

### 7. Kokoro — dialogue/TTS
Repository: https://github.com/hexgrad/kokoro
Apache-licensed model/weights, British English voices.
Recommendation: default offline dialogue generator where voice quality is acceptable.

### 8. MuseTalk — lip sync
Repository: https://github.com/TMElyralab/MuseTalk
MIT code; repository states trained model may be used commercially.
Minimum tested example: RTX 3050 Ti laptop / 4GB VRAM, ~5 minutes for an 8-second clip in fp16.
Recommendation: dialogue close-ups only; do not lip-sync every shot.

### 9. Whisper — transcription / subtitle QC
Repository: https://github.com/openai/whisper
MIT code and weights.
Approx GPU memory: tiny/base ~1GB, small ~2GB, medium ~5GB, turbo ~6GB, large ~10GB.
Recommendation: final subtitle and dialogue verification.

### 10. Real-ESRGAN / RIFE / FFmpeg
- Real-ESRGAN: restoration/upscale
- RIFE: frame interpolation; README reports 30+fps 2x 720p interpolation on 2080 Ti
- FFmpeg: deterministic assembly, audio mix, subtitles, encoding
Recommendation: mandatory post-production utilities.

## Revised Sigma Film Engine stack

CONTROL:
Sigma -> job manifest -> queue -> asset ledger

PREPRODUCTION:
screenplay -> scene graph -> shot manifest -> character/wardrobe/prop references

IMAGE/REFERENCE:
commercially cleared image model / reference workflow

VIDEO:
1. FramePack for long/continuous sequences
2. Wan2.2 TI2V-5B for high-value 720p hero shots
3. SkyReels 1.3B as an experimental long-form alternative
4. Avoid LTX-2.x as default until entity-level licence eligibility is confirmed

CHARACTER PERFORMANCE:
MuseTalk for lip sync where needed
portrait/motion tooling only after commercial licence audit

VOICE:
Kokoro British voices initially
upgrade/replace only where performance quality requires it

POST:
Whisper -> captions/QC
RIFE -> interpolation
Real-ESRGAN -> upscale/repair
FFmpeg + Blender/Kdenlive -> assembly/finishing

## Infrastructure conclusion

Known OVH role:
- appropriate as control plane;
- not appropriate for heavy video generation without a discrete supported GPU.

A read-only Sigma hardware audit workflow was committed:
.github/workflows/sigma-hardware-audit.yml

Current evidence:
- workflow correctly triggered in GitHub;
- job remains QUEUED on runs-on: self-hosted;
- therefore live runner/GPU capability is NOT VERIFIED.

Do not assume GPU exists until nvidia-smi/PCI evidence is captured.

## Practical compute target

Minimum useful rendering worker:
- NVIDIA GPU
- 24GB VRAM target
- >=32GB system RAM preferred
- >=150GB free SSD for models/cache/assets

Preferred:
- 24GB+ VRAM consumer/pro GPU for Wan2.2 TI2V-5B
- larger 48GB/80GB GPUs only for 14B/H100-class research paths

## Film production strategy

Do not attempt to generate 30 minutes as one AI-video job.
For a 30-minute narrative:
- generate reference-consistent stills and locations;
- reserve full generative motion for high-value shots;
- use FramePack/long-form methods for selected continuous sequences;
- use edit-driven motion, reaction shots, inserts, environments, screens and sound design;
- use deterministic FFmpeg/Kdenlive/Blender assembly;
- QC every generated shot before inclusion.

This turns the production problem from "buy 30 minutes of credits" into "operate a reusable GPU rendering pipeline."

## Next commissioning actions

1. Restore/verify self-hosted runner connectivity.
2. Capture actual OVH hardware audit.
3. Verify existing RunPod endpoint health without submitting a GPU job.
4. Build a dedicated film-worker container with ComfyUI + Wan2.2 + FramePack + Kokoro + Whisper + MuseTalk + post-processing.
5. Run a 5–10 second benchmark pack using PROVE YOU'RE HUMAN Scene 1.
6. Measure render time, VRAM, consistency and storage per shot.
7. Select the winning renderer(s).
8. Render the film scene-by-scene.
9. Assemble and QC final master.
