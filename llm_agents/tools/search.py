# Based on https://github.com/hwchase17/langchain/blob/master/langchain/utilities/serpapi.py

import os
import sys
from typing import Any

from llm_agents.tools.base import ToolInterface

from serpapi import GoogleSearch


def search(query: str) -> str:
    params: dict = {
        "engine": "google",
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "q": query,
        "api_key": os.environ["SERPAPI_API_KEY"]
    }

    with HiddenPrints():
        search = GoogleSearch(params)
        res = search.get_dict()

    return _process_response(res)


def _process_response(res: dict) -> str:
    """Process response from SerpAPI."""
    if "error" in res.keys():
        raise ValueError(f"Got error from SerpAPI: {res['error']}")
    if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
        toret = res["answer_box"]["answer"]
    elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
        toret = res["answer_box"]["snippet"]
    elif (
        "answer_box" in res.keys()
        and "snippet_highlighted_words" in res["answer_box"].keys()
    ):
        toret = res["answer_box"]["snippet_highlighted_words"][0]
    elif (
        "sports_results" in res.keys()
        and "game_spotlight" in res["sports_results"].keys()
    ):
        toret = res["sports_results"]["game_spotlight"]
    elif (
        "knowledge_graph" in res.keys()
        and "description" in res["knowledge_graph"].keys()
    ):
        toret = res["knowledge_graph"]["description"]
    elif "snippet" in res["organic_results"][0].keys():
        toret = res["organic_results"][0]["snippet"]

    else:
        toret = "No good search result found"
    return toret


class HiddenPrints:
    """Context manager to hide prints."""

    def __enter__(self) -> None:
        """Open file to pipe stdout to."""
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, *_: Any) -> None:
        """Close file that stdout was piped to."""
        sys.stdout.close()
        sys.stdout = self._original_stdout


class SerpAPITool(ToolInterface):
    """Tool for Google search results."""

    name = "Google Search"
    description = "Get specific information from a search query. Input should be a  question like 'How to add number in Clojure?'. Result will be the answer to the question."

    def use(self, input_text: str) -> str:
        return search(input_text) 


if __name__ == '__main__':
    s = SerpAPITool()
    res = s.use("Who is the pope in 2023?")
    print(res)
