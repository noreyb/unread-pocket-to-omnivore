import datetime
import os
import time

import requests
from requests.exceptions import SSLError
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

    # pocketからunreadなitemを取得する
    pocket_token = os.getenv("POCKET_TOKEN")
    consumer_key = os.getenv("POCKET_CONSUMER_KEY")
    pocket = PocketHandler(pocket_token, consumer_key)

    omnivore_token = os.getenv("OMNIVORE_API_KEY")
    client = OmnivoreQL(omnivore_token)
    cclient = COminvoreQL(omnivore_token)

    unread_items = pocket.get_items()
    for item in unread_items:
        url = item[0]
        date = item[1]

        # Error handling
        try:
            resp = requests.get(url)
        except SSLError as e:
            print(f"Skipping URL {url} due to SSL error: {e}")
            # pocketの記事をアーカイブする
            pocket.archive_item(url)
            continue
            
        if resp.status_code != requests.codes.ok:
            print(f"status_code: {resp.status_code}, url: {url}")
            # pocketの記事をアーカイブする
            pocket.archive_item(url)
            continue

        # ラベルの存在を確認する
        resp = client.get_labels()
        labels = resp["labels"]["labels"]
        labelname_id = {e["name"]: e["id"] for e in labels}
        time.sleep(1)

        label_id = None
        datelabel = date2datelabel(date)
        if datelabel not in list(labelname_id.keys()):
            # 既存のラベルが無ければ、新しいラベルを生成しlabel_idを取得する
            resp = cclient.create_label(datelabel)
            time.sleep(1)
            print(resp)
            label_id = resp["createLabel"]["label"]["id"]
        else:
            # 既存のラベルがあれば、そのlabel_idを取得する
            label_id = labelname_id[datelabel]

        # URLをomnivoreへsave
        resp = client.save_url(url)
        page_id = resp["saveUrl"]["clientRequestId"]
        time.sleep(1)

        # URLにラベルをセットする
        cclient.set_label(page_id, label_id)
        time.sleep(1)

        # pocketの記事をアーカイブする
        pocket.archive_item(url)


if __name__ == "__main__":
    main()
