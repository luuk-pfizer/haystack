import importlib
import logging

from typing import Dict, List, Any, Optional

from haystack import component, Document, default_to_dict, default_from_dict, DeserializationError
from haystack.document_stores.types import DocumentStore


logger = logging.getLogger(__name__)


@component
class FilterRetriever:
    """
    Retrieves documents that match the provided filters.
    """

    def __init__(self, document_store: DocumentStore, filters: Optional[Dict[str, Any]] = None):
        """
        Create the FilterRetriever component.

        :param document_store: An instance of InMemoryDocumentStore.
        :param filters: A dictionary with filters to narrow down the search space. Defaults to `None`.
        """
        self.document_store = document_store
        self.filters = filters

    def _get_telemetry_data(self) -> Dict[str, Any]:
        """
        Data that is sent to Posthog for usage analytics.
        """
        return {"document_store": type(self.document_store).__name__}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize this component to a dictionary.
        """
        docstore = self.document_store.to_dict()
        return default_to_dict(self, document_store=docstore, filters=self.filters)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterRetriever":
        """
        Deserialize this component from a dictionary.
        """
        init_params = data.get("init_parameters", {})
        if "document_store" not in init_params:
            raise DeserializationError("Missing 'document_store' in serialization data")
        if "type" not in init_params["document_store"]:
            raise DeserializationError("Missing 'type' in document store's serialization data")
        try:
            module_name, type_ = init_params["document_store"]["type"].rsplit(".", 1)
            logger.debug("Trying to import %s", module_name)
            module = importlib.import_module(module_name)
        except (ImportError, DeserializationError) as e:
            raise DeserializationError(
                f"DocumentStore of type '{init_params['document_store']['type']}' not correctly imported"
            ) from e

        docstore_class = getattr(module, type_)
        data["init_parameters"]["document_store"] = docstore_class.from_dict(data["init_parameters"]["document_store"])
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document])
    def run(self, filters: Optional[Dict[str, Any]] = None):
        """
        Run the FilterRetriever on the given input data.

        :param filters: A dictionary with filters to narrow down the search space.
            If not specified, the value provided at initialization is used.
        :return: The retrieved documents.
        """
        if filters is None:
            filters = self.filters

        return {"documents": self.document_store.filter_documents(filters=filters)}
