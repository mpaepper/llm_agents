# Based on https://raw.githubusercontent.com/hwchase17/langchain/master/langchain/utilities/google_search.py

import os
from typing import Any
from llm_agents.tools.base import ToolInterface
from googleapiclient.discovery import build


"""Wrapper for Google Search API.

Adapted from: Instructions adapted from https://stackoverflow.com/questions/
37083058/
programmatically-searching-google-in-python-using-custom-search

1. Install google-api-python-client
- If you don't already have a Google account, sign up.
- If you have never created a Google APIs Console project,
read the Managing Projects page and create a project in the Google API Console.
- Install the library using pip install google-api-python-client
The current version of the library is 2.70.0 at this time

2. To create an API key:
- Navigate to the APIs & Services→Credentials panel in Cloud Console.
- Select Create credentials, then select API key from the drop-down menu.
- The API key created dialog box displays your newly created key.
- You now have an API_KEY

3. Setup Custom Search Engine so you can search the entire web
- Create a custom search engine in this link.
- In Sites to search, add any valid URL (i.e. www.stackoverflow.com).
- That’s all you have to fill up, the rest doesn’t matter.
In the left-side menu, click Edit search engine → {your search engine name}
→ Setup Set Search the entire web to ON. Remove the URL you added from
  the list of Sites to search.
- Under Search engine ID you’ll find the search-engine-ID.

4. Enable the Custom Search API
- Navigate to the APIs & Services→Dashboard panel in Cloud Console.
- Click Enable APIs and Services.
- Search for Custom Search API and click on it.
- Click Enable.
URL for it: https://console.cloud.google.com/apis/library/customsearch.googleapis
.com
"""


def _google_search_results(params) -> list[dict[str, Any]]:
    service = build("customsearch", "v1", developerKey=params['api_key'])
    res = service.cse().list(
        q=params['q'], cx=params['cse_id'], num=params['max_results']).execute()
    return res.get('items', [])


def search(query: str) -> str:
    params: dict = {
        "q": query,
        "cse_id": os.environ["GOOGLE_CSE_ID"],
        "api_key": os.environ["GOOGLE_API_KEY"],
        "max_results": 10
    }

    res = _google_search_results(params)
    snippets = []
    if len(res) == 0:
        return "No good Google Search Result was found"
    for result in res:
        if "snippet" in result:
            snippets.append(result["snippet"])

    return " ".join(snippets)


class GoogleSearchTool(ToolInterface):
    """Tool for Google search results."""

    name: str = "Google Search"
    description: str = "Get specific information from a search query. Input should be a question like 'How to add number in Clojure?'. Result will be the answer to the question."

    def use(self, input_text: str) -> str:
        return search(input_text)


if __name__ == '__main__':
    s = GoogleSearchTool()
    res = s.use("Who was the pope in 2023?")
    print(res)
