from .radiology_document_classifier import RadiologyDocumentClassifier
from .emergency_document_classifier import EmergencyDocumentClassifier
from .discharge_document_classifier import DischargeDocumentClassifier


def get_relevant_sections():
    from .emergency_document_classifier import RELEVANT_SECTIONS as ed_sections
    from .discharge_document_classifier import RELEVANT_SECTIONS as dc_sections

    relevant_sections = {
        "emergency": set(),
        "radiology": set(),
        "discharge": set(),
    }
    for (_, sections) in ed_sections.items():
        relevant_sections["emergency"].update(set(sections))
    for section in ["impression", "imaging"]:
        relevant_sections["radiology"].add(section)
    for section in dc_sections:
        relevant_sections["discharge"].add(section)

    return relevant_sections