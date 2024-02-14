from .detail_court import main as process_detail_court_collection
from .detail_institution import main as process_detail_institution_collection
from .detail_place import main as process_detail_place_collection
from .detail_source import main as process_detail_source_collection
from .detail_person import main as process_detail_person_collection

__all__ = [
    "process_detail_court_collection",
    "process_detail_institution_collection",
    "process_detail_place_collection",
    "process_detail_source_collection",
    "process_detail_person_collection",
]
