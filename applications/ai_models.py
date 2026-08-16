import os
import io

import cv2
import numpy as np
import torch
from PIL import Image, ImageOps
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from transformers import CLIPModel, CLIPProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NOTE: blur is measured on the FULL-resolution image, before this resize.
# Laplacian variance shrinks as you downscale (you're smoothing away the
# high-frequency detail the metric depends on), so measuring it after
# resize makes genuinely sharp photos look blurry and forces you to keep
# re-tuning the threshold every time MAX_DIMENSION changes.
MAX_DIMENSION = 640


# =========================
# Load all models ONCE at import time
# =========================
LANDMARKER_MODEL_PATH = os.path.join(BASE_DIR, "face_landmarker.task")

_landmarker = mp_vision.FaceLandmarker.create_from_options(
    mp_vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=LANDMARKER_MODEL_PATH),
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=True,
        num_faces=2,
        min_face_detection_confidence=0.6,
        min_face_presence_confidence=0.6,
        min_tracking_confidence=0.6,
        running_mode=mp_vision.RunningMode.IMAGE,
    )
)

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
_clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
_clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
_clip_model.eval()

# Balanced, short, parallel-phrased labels (CLIP's text encoder is sensitive
# to length/style mismatches between labels being compared).
LABEL_CLEAR = "a real unedited photograph of an actual human face"
# Broadened to also cover glossy 3D-rendered / CGI / video-game-style avatars
# (Pixar-like renders), not just flat 2D cartoon or anime drawings. The
# original wording under-matched stylized 3D renders, letting them slip
# past as "real".
LABEL_CARTOON = "a cartoon, anime, 3D-rendered, CGI, or digitally illustrated character face, not a real photo"
LABEL_ANIMAL = "a photo of a cat or other animal face"
LABEL_MASK = "a face wearing a mask over the nose and mouth"
LABEL_SUNGLASSES = "a face wearing sunglasses"
LABEL_HAND = "a face partly covered by a hand or object"

CLIP_LABELS = [LABEL_CLEAR, LABEL_CARTOON, LABEL_ANIMAL, LABEL_MASK, LABEL_SUNGLASSES, LABEL_HAND]

# These labels are fixed. Encoding them at startup avoids running CLIP's text
# encoder for every upload.
with torch.inference_mode():
    _clip_text_inputs = _clip_processor(text=CLIP_LABELS, return_tensors="pt", padding=True)
    # Transformers 5 returns a BaseModelOutputWithPooling here; its
    # pooler_output already contains CLIP's projected text features.
    _clip_text_features = _clip_model.get_text_features(**_clip_text_inputs).pooler_output
    _clip_text_features = _clip_text_features / _clip_text_features.norm(dim=-1, keepdim=True)


# =========================
# Image loading (EXIF-safe + resized)
# =========================
def load_image(image_source):
    """
    Returns (small_bgr, full_bgr):
      - small_bgr: downscaled to MAX_DIMENSION, used for face detection / CLIP
      - full_bgr:  original resolution (post EXIF-transpose), used for blur check
    """
    pil_img = Image.open(io.BytesIO(image_source) if isinstance(image_source, bytes) else image_source)
    pil_img = ImageOps.exif_transpose(pil_img)  # fix sideways/upside-down phone photos
    pil_img = pil_img.convert("RGB")

    full_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    w, h = pil_img.size
    scale = MAX_DIMENSION / max(w, h)
    if scale < 1:
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    small_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return small_bgr, full_bgr


# =========================
# Brightness / Blur (cheap, run first)
# =========================
def check_brightness(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    if brightness < 50:
        return False, "Image is too dark"
    if brightness > 230:
        return False, "Image is overexposed"
    return True, None


def check_blur(img):
    # Measured on the full-resolution image — see MAX_DIMENSION note above.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(blur)
    if blur < 45:
        return False, "Image is blurry"
    return True, None


# =========================
# Face geometry + pose
# =========================
def run_face_landmarker(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return _landmarker.detect(mp_image)


def check_face_and_pose(img, result, max_yaw_deg=24, max_pitch_deg=24, max_roll_deg=26):
    if not result.face_landmarks:
        return False, "No face detected", None
    if len(result.face_landmarks) > 1:
        return False, "Multiple faces detected — only one person allowed", None

    h, w, _ = img.shape
    landmarks = result.face_landmarks[0]
    xs = [lm.x * w for lm in landmarks]
    ys = [lm.y * h for lm in landmarks]
    face_w, face_h = max(xs) - min(xs), max(ys) - min(ys)
    face_ratio = (face_w * face_h) / (w * h)

    # Allow a little more background than a tightly cropped passport photo,
    # while still requiring enough detail for the downstream checks.
    if face_ratio < 0.085:
        return False, "Face is too far away", None
    if face_ratio > 0.80:
        return False, "Face is too close / cropped", None

    if not result.facial_transformation_matrixes:
        return False, "Could not estimate head pose", None

    rot = np.array(result.facial_transformation_matrixes[0])[:3, :3]
    sy = np.sqrt(rot[0, 0] ** 2 + rot[1, 0] ** 2)
    pitch = np.degrees(np.arctan2(-rot[2, 0], sy))
    yaw = np.degrees(np.arctan2(rot[1, 0], rot[0, 0]))
    roll = np.degrees(np.arctan2(rot[2, 1], rot[2, 2]))

    if abs(yaw) > max_yaw_deg:
        return False, "Please use a photo where your face is generally toward the camera", None
    if abs(pitch) > max_pitch_deg:
        return False, "Please use a photo with your head roughly level and facing the camera", None
    if abs(roll) > max_roll_deg:
        return False, "Please use a photo with your head roughly level and facing the camera", None

    bbox = (min(xs), min(ys), face_w, face_h)
    return True, None, bbox


def crop_face(img, bbox, margin=0.25):
    h, w, _ = img.shape
    x, y, bw, bh = bbox
    mx, my = bw * margin, bh * margin
    x0, y0 = max(int(x - mx), 0), max(int(y - my), 0)
    x1, y1 = min(int(x + bw + mx), w), min(int(y + bh + my), h)
    return img[y0:y1, x0:x1]


# =========================
# ONE CLIP forward pass, scored as THREE independent comparisons
# (cartoon-vs-real, animal-vs-real, occlusion-vs-clear) instead of one
# 6-way softmax. A combined softmax makes "real face" compete against every
# rejection category at once, which dilutes its score even for genuine
# clear photos — that's what was causing false rejections earlier.
#
# NOTE ON THE ANIMAL CHECK: this is CLIP-only. MediaPipe's FaceLandmarker
# can occasionally produce landmarks on a front-facing animal face, and
# nothing downstream re-verifies "this is a human" independently — the
# animal/cartoon labels below are the only defense. A dedicated face
# detector as a second opinion would be more robust, but costs extra
# latency; CLIP-only is the current tradeoff for speed.
# =========================
CARTOON_REJECT_THRESHOLD = 0.966     # binary vs. the broadened LABEL_CARTOON above
ANIMAL_REJECT_THRESHOLD = 0.72    # high confidence only; avoids false positives
OCCLUSION_REJECT_THRESHOLD = 0.55
SUNGLASSES_REJECT_THRESHOLD = 0.78  # ordinary clear glasses should pass

def check_face_clip(face_crop):
    rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    image_inputs = _clip_processor(images=pil_img, return_tensors="pt")
    with torch.inference_mode():
        # Same API behaviour as get_text_features above.
        image_features = _clip_model.get_image_features(pixel_values=image_inputs["pixel_values"]).pooler_output
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        logits = (image_features @ _clip_text_features.T * _clip_model.logit_scale.exp())[0]

    clear, cartoon, animal, mask, sunglasses, hand = logits.tolist()

    # --- Cartoon check: binary, clear vs cartoon only ---
    p_cartoon = torch.softmax(torch.tensor([clear, cartoon]), dim=0)[1].item()

    # --- Animal check: binary, clear vs animal only ---
    p_animal = torch.softmax(torch.tensor([clear, animal]), dim=0)[1].item()

    # --- Occlusion check: 4-way among clear/mask/sunglasses/hand ---
    occ_probs = torch.softmax(torch.tensor([clear, mask, sunglasses, hand]), dim=0)
    p_clear_occ, p_mask, p_sunglasses, p_hand = occ_probs.tolist()

    print(f"CLIP cartoon={p_cartoon:.3f} animal={p_animal:.3f} | clear={p_clear_occ:.3f} "
          f"mask={p_mask:.3f} sunglasses={p_sunglasses:.3f} hand={p_hand:.3f}")

    if p_cartoon > CARTOON_REJECT_THRESHOLD:
        return False, "We could not confirm a clear human face in this photo"
    if p_animal > ANIMAL_REJECT_THRESHOLD:
        return False, "Please upload a photo showing one clear human face"

    best_occlusion = max(p_mask, p_sunglasses, p_hand)
    if best_occlusion > OCCLUSION_REJECT_THRESHOLD and best_occlusion > p_clear_occ:
        if p_mask == best_occlusion:
            return False, "Face mask detected — please remove it for the photo"
        # CLIP can label normal prescription glasses as sunglasses. Require a
        # much stronger sunglasses signal before rejecting; clear glasses pass.
        if p_sunglasses == best_occlusion and p_sunglasses > SUNGLASSES_REJECT_THRESHOLD and p_sunglasses > p_clear_occ + 0.20:
            return False, "Sunglasses detected — please remove them for the photo"
        if p_hand == best_occlusion:
            return False, "Face is partially covered — please ensure your full face is visible"

    return True, None


# =========================
# Main Validator
# =========================
def validate_passport_image(image_source):
    try:
        small_img, full_img = load_image(image_source)
    except Exception:
        return False, "Cannot read image"

    ok, msg = check_brightness(small_img)
    if not ok:
        return False, msg

    ok, msg = check_blur(full_img)  # full resolution — see note on MAX_DIMENSION
    if not ok:
        return False, msg

    result = run_face_landmarker(small_img)
    ok, msg, bbox = check_face_and_pose(small_img, result)
    if not ok:
        return False, msg

    face_crop = crop_face(small_img, bbox)

    ok, msg = check_face_clip(face_crop)  # cartoon + animal + occlusion, one CLIP call
    if not ok:
        return False, msg

    return True, "Valid passport image"


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"
    print(validate_passport_image(path))
