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

    def set_label(self, label: str):
        pass

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

    profile = client.get_labels()
    print(profile)

    cclient = COminvoreQL(api_key)
    label = "hogehoge"
    print(cclient.create_label(label))


if __name__ == "__main__":
    main()
