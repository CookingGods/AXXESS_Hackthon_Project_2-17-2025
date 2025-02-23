from inference_sdk import InferenceHTTPClient

client = InferenceHTTPClient(
    api_url="http://localhost:9001", # use local inference server
    api_key="Ups9KQLQ0H6FQKTlonqT"
)

result = client.run_workflow(
    workspace_name="axxcess-2025",
    workflow_id="custom-workflow",
    images={
        "image": "Bruises_share.jpg"
    }
)

print(result)
