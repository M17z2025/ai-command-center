# THE LINE — Open-Source Generation Pipeline

## Objective
Generate S01E01 using the existing ALISHA AI Movie stack as the primary route, with paid providers optional.

## Runtime architecture
Sigma Command Center -> shot queue -> GPU worker -> ComfyUI workflow -> model output -> QC -> approved assets -> FFmpeg/Blender assembly.

## Primary open-source tools
- ComfyUI
- Wan / Wan2.x
- LTX-Video / LTX-AV
- AnimateDiff
- Wav2Lip
- Kokoro / Chatterbox
- ACE-Step
- Real-ESRGAN / GFPGAN
- Blender
- FFmpeg

## Shot states
PLANNED -> KEYFRAME_READY -> GENERATING -> GENERATED -> QC_FAIL / QC_PASS -> EDIT_READY -> LOCKED

## Asset IDs
Characters: CHAR-TJ, CHAR-KAI, CHAR-AMIRA, CHAR-MARCUS, CHAR-TOMMY, CHAR-NOAH, CHAR-SOFIA, CHAR-ELLIE, DOG-ATLAS
Locations: LOC-PATEL-GARAGE, LOC-PATEL-HOME, LOC-VALE, LOC-FOOTBALL, LOC-HAWTHORNE, LOC-BLACKTHORN, LOC-DOCKLANDS
Vehicles: VEH-TJ-EV1, VEH-MARCUS-TORCAL, VEH-BLACKTHORN-SUV1

## Generation principle
1. Create a locked still keyframe.
2. Validate identity, clothing, location, dog and vehicle.
3. Animate only the approved keyframe.
4. Keep shots short.
5. Repair or regenerate failures rather than hiding them with aggressive grading.

## Anti-AI finish
Every output must pass anatomy, face identity, dog markings, vehicle geometry, reflections, physics, motion, camera plausibility, materials, lip sync and audio realism.

## Pilot first batch
1. TJ + Atlas garage portrait
2. Patel Performance wide
3. Atlas reacting to Marcus arrival
4. Bentley Torcal arrival
5. Tommy football ground
6. Hawthorne Estate wide
7. Noah evidence wall
8. Docklands chase keyframes
9. THE LINE case insert
10. Ravi/Marcus/Victor archival photograph
