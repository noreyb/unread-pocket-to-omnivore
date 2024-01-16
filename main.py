import datetime
import os
import time

import requests
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from omnivoreql import OmnivoreQL


# Complementary omnivoreql
class COminvoreQL:
    def __init__(
        self,
        api_token: str,
        graphql_endpoint: str = "https://api-prod.omnivore.app/api/graphql",
    ):
        transport = RequestsHTTPTransport(
            url=graphql_endpoint,
            headers={
                "Content-type": "application/json",
                "Authorization": api_token,
            },
            use_json=True,
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def set_label(self, page_id, label_id):
        mutation_set_labels = gql(
            """
            mutation SetLabels($input: SetLabelsInput!) {
              setLabels(input: $input) {
                ... on SetLabelsSuccess {
                  labels {
                    ...LabelFields
                  }
                }
                ... on SetLabelsError {
                  errorCodes
                }
              }
            }

            fragment LabelFields on Label {
              id
              name
              color
              description
              createdAt
            }
        """
        )

        variables = {"input": {"labelIds": [label_id], "pageId": page_id}}
        return self.client.execute(mutation_set_labels, variable_values=variables)

    def create_label(self, label: str, description: str = "", color: str = "#ABB8C3"):
        mutation = gql(
            """
            mutation CreateLabel($input: CreateLabelInput!) {
                createLabel(input: $input) {
                    ... on CreateLabelSuccess {
                      label {
                        id
                        name
                        color
                        description
                        createdAt
                    }
                }
                    ... on CreateLabelError {
                        errorCodes
                }
            }
        }
        """
        )

        variables = {
            "input": {
                "name": label,
                "color": "#ABB8C3",
                "description": "",
            }
        }
        return self.client.execute(mutation, variable_values=variables)


class PocketHandler:
    def __init__(self, token, consumer_key):
        self.token = token
        self.consumer_key = consumer_key

    def archive_item(self, url):
        # get item_id from url
        endpoint = "https://getpocket.com/v3/get"
        resp = requests.post(
            endpoint,
            data={
                "consumer_key": self.consumer_key,
                "access_token": self.token,
                "search": url,
            },
        )
        # Error handling
        if resp.status_code != requests.codes.ok:
            raise Exception(f"status_code: {resp.status_code}, url: {url}")

        resp = resp.json()
        time.sleep(1)
        if resp["status"] == 2:
            # This item has been deleted
            return None
        item_id = resp["list"][list(resp["list"].keys())[0]]["item_id"]

        # archive item
        endpoint = "http://getpocket.com/v3/send"
        data = {
            "consumer_key": self.consumer_key,
            "access_token": self.token,
            "actions": [
                {
                    "action": "archive",
                    "item_id": item_id,
                }
            ],
        }
        headers = {"Content-type": "application/json", "X-accept": "application/json"}
        resp = requests.post(endpoint, json=data, headers=headers)
        if resp.status_code != requests.codes.ok:
            raise Exception(f"status_code: {resp.status_code}, url: {url}")
        time.sleep(1)

    def get_items(
        self, state="unread", content_type="article", sort="oldest", count="10"
    ):
        # get item_id from url
        endpoint = "https://getpocket.com/v3/get"
        resp = requests.post(
            endpoint,
            data={
                "consumer_key": self.consumer_key,
                "access_token": self.token,
                "state": state,
                "contentType": content_type,
                "sort": sort,
                "count": count,
            },
        )
        time.sleep(1)

        # Error handling
        if resp.status_code != requests.codes.ok:
            raise Exception("Something is happen to access pocket api.")

        resp = resp.json()
        urls_times = []
        for e in list(resp["list"].values()):
            urls_times.append(
                (
                    e["given_url"],
                    datetime.datetime.fromtimestamp(int(e["time_added"])).strftime(
                        "%Y-%m"
                    ),
                )
            )
        return urls_times


def date2datelabel(strdate: str):
    return f"ZZ-{strdate}"


def main():
    load_dotenv()
    api_key = os.getenv("OMNIVORE_API_KEY")
    client = OmnivoreQL(api_key)
    resp = client.save_url("https://www.google.com/")
    page_id = resp["clientRequestId"]

    cclient = COminvoreQL(api_key)
    label = "hogehoge"
    print(cclient.create_label(label))


if __name__ == "__main__":
    main()
