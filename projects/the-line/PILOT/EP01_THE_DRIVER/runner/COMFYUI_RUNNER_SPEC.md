# THE LINE — ComfyUI / Open-Source Runner Specification v1

## Flow
Sigma Shot Queue -> Worker API -> ComfyUI -> model workflow -> output registry -> QC -> approved asset store -> FFmpeg/Blender edit.

## Required workflows
WF01_KEYFRAME_CHARACTER
WF02_KEYFRAME_LOCATION
WF03_I2V_DIALOGUE
WF04_I2V_ACTION_EV
WF05_LIPSYNC
WF06_FACE_REPAIR
WF07_UPSCALE
WF08_SOUND_VOICE
WF09_MUSIC
WF10_ASSEMBLY

## Model routing
- Keyframes: SDXL-class / Flux-class or best locally available photoreal model.
- Video: Wan / Wan2.x primary; LTX-Video/LTX-AV secondary; AnimateDiff for controlled short motion where appropriate.
- Lip sync: Wav2Lip-class pipeline.
- Voice: Kokoro / Chatterbox.
- Music: ACE-Step.
- Restoration: GFPGAN only when needed; Real-ESRGAN for upscale.
- Assembly: FFmpeg; Blender for VFX/compositing.

## Shot manifest schema
shot_id
scene_id
status
prompt
negative_prompt
character_refs[]
location_ref
wardrobe_look
vehicle_ref
animal_ref
start_frame
end_frame
duration_s
fps
resolution
seed
model
workflow_version
continuity_state
qc_status
output_path

## Policy
Never overwrite approved assets. Version every regeneration. Preserve seed/model/workflow version for reproducibility.
