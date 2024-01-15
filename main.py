import os
import uuid

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
