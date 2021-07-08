DOMAINS = ("emergency", "radiology", "discharge",)
import os
from pathlib import Path

CONFIG_FILES = {
    "discharge": os.path.join(Path(__file__).resolve().parents[0], "resources/configs/discharge.json"),
    "radiology": os.path.join(Path(__file__).resolve().parents[0], "resources/configs/radiology.json"),
    "emergency": os.path.join(Path(__file__).resolve().parents[0], "resources/configs/emergency.json"),

}

TARGET_CONCEPTS = ("PNEUMONIA", "OPACITY", "INFILTRATE", "CONSOLIDATION", "HOSPITAL_ACQUIRED_PNEUMONIA",)
PNEUMONIA_CONCEPTS = ("PNEUMONIA", "HOSPITAL_ACQUIRED_PNEUMONIA",)
FINDINGS_CONCEPTS = ("OPACITY", "INFILTRATE", "CONSOLIDATION",)
