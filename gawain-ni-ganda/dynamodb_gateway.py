import boto3
import itertools
from boto3.dynamodb.conditions import Key

class DynamodbGateway:
    @classmethod
    def grouper(cls, iterable, n, fillvalue=None):
        "Collect data into fixed-length chunks or blocks"
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    
    @classmethod
    def upsert(cls, table_name, mapping_data, primary_keys):
        print(f"Inserting into table {table_name}")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        for group in cls.grouper(mapping_data, 100):
            batch_entries = list(filter(None.__ne__, group))

            print("=====")
            print("WRITING THIS BATCH in batches of 100")
            print(batch_entries)
            print("=====")

            with table.batch_writer(overwrite_by_pkeys=primary_keys) as batch:
                for entry in batch_entries:
                    batch.put_item(
                        Item = entry
                    )

    @classmethod
    def scan_table(cls, table_name, last_evaluated_key=None):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        items = []

        if last_evaluated_key == None:
            response = table.scan()
            items.extend(response.get('Items'))
        else:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
            items.extend(response.get('Items'))

        if 'Items' not in response:
            raise Exception(f"There is no objects for this object on table {table_name}")

        if 'LastEvaluatedKey' not in response:
            response["LastEvaluatedKey"] = None

        while ("LastEvaluatedKey" in response) and (response["LastEvaluatedKey"] != None):
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])

            items.extend(response.get('Items'))

            print("==============================================")
            print("ITEMS FROM THE RESPONSE -- INSIDE THE LOOP")
            print(response)
            print(f"item_count: {len(items)}, LastEvaluatedKey: {response.get('LastEvaluatedKey')}")


        return {
            "items": items,
            "last_evaluated_key": response["LastEvaluatedKey"]
        }

    @classmethod
    def query_by_partition_key(cls, table_name, partition_key_name, partition_key_query_value, attributes="ALL_ATTRIBUTES"):
        print(f"Reading from table {table_name}")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        items = []

        if attributes == "ALL_ATTRIBUTES":
            resp = table.query(
                KeyConditionExpression=Key(partition_key_name).eq(partition_key_query_value),
            )
        else:
            select_data = cls.process_projection_expression(attributes)

            resp = table.query(
                KeyConditionExpression=Key(partition_key_name).eq(partition_key_query_value),
                Select=select_data["select"],
                ProjectionExpression=select_data["expression"],
                ExpressionAttributeNames=select_data["expression_attr"]
            )

        items.extend(resp.get('Items'))

        print("==============================================")
        print("ITEMS FROM THE RESPONSE -- BEFORE THE LOOP")
        print(resp)
        print(f"item_count: {len(items)}, LastEvaluatedKey: {resp.get('LastEvaluatedKey')}")
        print("NO LOOP ANYMORE - COMMENTED OUT")

        return {
            "items": items,
            "last_evaluated_key": resp.get('LastEvaluatedKey')
        }
    
    @classmethod
    def delete_items(cls, table_name, keys_to_delete):
        """
        Delete multiple items from a DynamoDB table using a list of primary keys.

        Parameters:
        - table_name (str): Name of the DynamoDB table.
        - keys_to_delete (list): List of dictionaries where each dictionary represents the primary key(s) of an item to delete.
        """
        print(f"Deleting items from table {table_name}")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)

        with table.batch_writer() as batch:
            for key in keys_to_delete:
                batch.delete_item(Key=key)

        print(f"Deleted items with keys: {keys_to_delete}")