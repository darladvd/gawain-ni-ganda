import json
import uuid
import os
from dynamodb_gateway import DynamodbGateway

TABLE_NAME = os.getenv("DYNAMODB_CARDS_TABLE_NAME")

def create_task(event, context):
    body = json.loads(event["body"])
    task_id = str(uuid.uuid4())

    task = {
        "task_id": task_id,
        "title": body.get("title", ""),
        "description": body.get("description", ""),
        "status": body.get("status", "To Do")
    }

    DynamodbGateway.upsert(
        table_name=TABLE_NAME,
        mapping_data=[task],
        primary_keys=["task_id"]
    )

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Task created successfully",
            "task": task
        })
    }
    return response

def list_task(event, context):
    tasks = DynamodbGateway.scan_table(
        table_name=TABLE_NAME
    )

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Tasks retrieved successfully",
            "tasks": tasks["items"]
        })
    }

    return response

def get_task(event, context):
    task_id = event["pathParameters"]["task_id"]

    task = DynamodbGateway.query_by_partition_key(
        table_name=TABLE_NAME,
        partition_key_name="task_id",
        partition_key_query_value=task_id
    )

    if not task["items"]:
        response = {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Task not found",
                "message": "Task not found"
            })
        }
    else:
        response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Task retrieved successfully",
                "task": task["items"][0]
            })
        }

    return response

def update_task(event, context):
    body = json.loads(event["body"])
    task_id = event["pathParameters"]["task_id"]

    existing_task = DynamodbGateway.query_by_partition_key(
        table_name=TABLE_NAME,
        partition_key_name="task_id",
        partition_key_query_value=task_id
    )

    if not existing_task["items"]:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Task not found",
                "message": "Task not found"
            })
        }

    valid_statuses = ["To Do", "In Progress", "Done"]
    status = body.get("status")
    if status and status not in valid_statuses:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Invalid status. Valid values are: {', '.join(valid_statuses)}",
                "message": "Invalid status"
            })
        }

    task = existing_task["items"][0]
    task["title"] = body.get("title", task["title"])
    task["description"] = body.get("description", task["description"])
    task["status"] = status if status else task["status"]

    DynamodbGateway.upsert(
        table_name=TABLE_NAME,
        mapping_data=[task],
        primary_keys=["task_id"]
    )

    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Task updated successfully",
            "task": task
        })
    }
    return response

def delete_task(event, context):
    task_id = event["pathParameters"].get("task_id")
    
    if not task_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "task_id path parameter is required"})
        }

    key_to_delete = {"task_id": task_id}

    DynamodbGateway.delete_items(table_name=TABLE_NAME, keys_to_delete=[key_to_delete])

    response = {
        "statusCode": 200,
        "body": json.dumps({"message": f"Successfully deleted task with task_id: {task_id}"})
    }

    return response
