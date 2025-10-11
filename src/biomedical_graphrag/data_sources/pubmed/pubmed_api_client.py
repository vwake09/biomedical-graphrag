import time

from Bio import Entrez

from biomedical_graphrag.config import settings


class PubMedAPIClient:
    """
    PubMed E-utilities API client for fetching paper IDs, details, and citations.
    """

    def __init__(self) -> None:
        """
        Initialize the PubMed API client with email and API key.
        Args:
            email (str | None): The email address to use for the Entrez API.
            api_key (str | None): The API key to use for the Entrez API.
        Returns:
            None
        """
        self.email = settings.pubmed.email
        self.api_key = settings.pubmed.api_key

        if self.email:
            Entrez.email = self.email  # type: ignore[assignment]
        if self.api_key:
            Entrez.api_key = self.api_key  # type: ignore[assignment]

    def _rate_limit(self) -> None:
        """
        Apply rate limiting to the Entrez API requests.
        Args:
            None
        Returns:
            None
        """
        time.sleep(0.1 if Entrez.api_key else 0.34)

    def search(self, query: str, max_results: int = 100, sort: str = "relevance") -> list[str]:
        """
        Search for papers in the PubMed database.
        Args:
            query (str): The search query.
            max_results (int): The maximum number of results to return.
            sort (str): The sort order of the results.
        Returns:
            list[str]: A list of PubMed IDs (PMIDs) matching the search query.
        """
        self._rate_limit()
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort=sort)
        record = Entrez.read(handle)
        pmids = record.get("IdList", [])
        handle.close()
        return pmids

    def fetch_papers(self, pmid_list: list[str]) -> list[dict]:
        """
        Fetch paper details from PubMed using a list of PMIDs.
        Args:
            pmid_list (list[str]): A list of PubMed IDs (PMIDs) to fetch.
        Returns:
            list[dict]: A list of dictionaries containing paper details.
        """
        if not pmid_list:
            return []
        self._rate_limit()
        ids = ",".join(pmid_list)
        handle = Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        return records.get("PubmedArticle", [])

    def fetch_citations(self, pmid: str) -> dict[str, list[str]]:
        """
        Fetch citations for a given PubMed ID (PMID).
        Args:
            pmid (str): The PubMed ID to fetch citations for.
        Returns:
            dict[str, list[str]]: A dictionary containing lists of cited by and references PMIDs.
        """
        result: dict[str, list[str]] = {"cited_by": [], "references": []}
        self._rate_limit()
        handle = Entrez.elink(
            dbfrom="pubmed", db="pubmed", id=pmid, linkname="pubmed_pubmed_citedin"
        )
        citing_record = Entrez.read(handle)
        handle.close()
        if citing_record[0].get("LinkSetDb"):
            result["cited_by"] = [link["Id"] for link in citing_record[0]["LinkSetDb"][0]["Link"]]
        self._rate_limit()
        handle = Entrez.elink(dbfrom="pubmed", db="pubmed", id=pmid, linkname="pubmed_pubmed_refs")
        refs_record = Entrez.read(handle)
        handle.close()
        if refs_record[0].get("LinkSetDb"):
            result["references"] = [link["Id"] for link in refs_record[0]["LinkSetDb"][0]["Link"]]
        return result
