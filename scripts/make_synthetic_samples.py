"""Generate SYNTHETIC test files with FAKE patient identifiers, to demonstrate de-identification.

No real patient data. The images are drawn shapes that only resemble a lung ultrasound view,
with a made-up name / MRN / date of birth printed in the header band (where real scanners print them).

Outputs in data/samples/:
  synthetic_fake_phi_lung.png   PNG with fake burned-in identifiers + fake EXIF tags
  synthetic_fake_phi_clip.mp4   2-second clip with a "sliding" pleural line + burned-in identifiers
  synthetic_fake_phi.dcm        DICOM with fake PatientName / PatientID / BirthDate tags
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "data" / "samples"
FAKE = {"name": "DOE^JANE", "mrn": "MRN 00012345", "dob": "DOB 01/02/1960"}   # obviously fake
W, H = 640, 480


def lung_frame(t: float = 0.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = rng.normal(28, 10, (H, W)).clip(0, 255)
    pleura_y = 150
    img[60:pleura_y - 8] += rng.normal(35, 12, (pleura_y - 68, W))          # chest wall soft tissue
    img[pleura_y - 3:pleura_y + 3] = 225                                     # pleural line
    shimmer = (rng.random(W) * 60 * (0.5 + 0.5 * np.sin(t * 6 + np.arange(W) / 9))).astype(float)
    img[pleura_y + 3:pleura_y + 9] += shimmer                                # "lung sliding" texture
    for k in (2, 3):                                                         # A-lines
        y = pleura_y + (pleura_y - 60) * (k - 1)
        if y < H - 5:
            img[y - 2:y + 2] += 90 / k
    for x0 in (90, 470):                                                     # ribs + acoustic shadows
        img[pleura_y - 40:pleura_y - 28, x0:x0 + 80] = 200
        img[pleura_y - 28:, x0:x0 + 80] *= 0.15
    img = img.clip(0, 255).astype(np.uint8)
    rgb = np.stack([img] * 3, axis=-1)
    cv2.rectangle(rgb, (0, 0), (W, 44), (20, 20, 20), -1)                    # scanner header band
    cv2.putText(rgb, f"{FAKE['name']}  {FAKE['mrn']}  {FAKE['dob']}", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(rgb, "L12-4  D 4.0cm  G 52", (W - 200, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    return rgb


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    img = Image.fromarray(lung_frame())
    exif = Image.Exif()
    exif[0x010E] = f"Patient {FAKE['name']} {FAKE['mrn']}"   # ImageDescription
    exif[0x013B] = "Dr. Fake Sonographer"                    # Artist
    img.save(OUT / "synthetic_fake_phi_lung.png", exif=exif)

    vw = cv2.VideoWriter(str(OUT / "synthetic_fake_phi_clip.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 15, (W, H))
    for i in range(30):
        vw.write(cv2.cvtColor(lung_frame(i / 15, seed=i), cv2.COLOR_RGB2BGR))
    vw.release()

    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.6.1"   # Ultrasound Image Storage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset(str(OUT / "synthetic_fake_phi.dcm"), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.PatientName, ds.PatientID, ds.PatientBirthDate = FAKE["name"], "00012345", "19600102"
    ds.InstitutionName, ds.StudyDate = "Fake General Hospital", "20261118"
    ds.Modality, ds.SOPClassUID, ds.SOPInstanceUID = "US", meta.MediaStorageSOPClassUID, meta.MediaStorageSOPInstanceUID
    gray = cv2.cvtColor(lung_frame(), cv2.COLOR_RGB2GRAY)
    ds.Rows, ds.Columns = gray.shape
    ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, "MONOCHROME2"
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 8, 8, 7, 0
    ds.PixelData = gray.tobytes()
    ds.save_as(OUT / "synthetic_fake_phi.dcm", enforce_file_format=True)
    print("Wrote:", *sorted(p.name for p in OUT.iterdir()), sep="\n  ")


if __name__ == "__main__":
    main()
