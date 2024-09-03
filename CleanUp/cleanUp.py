import boto3
import time

"""
#region Delete Cloudformation
cfn_client = boto3.client('cloudformation')

# Get all active stacks
client_list = cfn_client.list_stacks(
    StackStatusFilter = ['CREATE_COMPLETE','UPDATE_COMPLETE']
    )
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation/client/list_stacks.html


#count = len(client_list["StackSummaries"])

# StackSummaries fetches stacks in order of creation time with the first being the last created
# Deletion will be from top down
for stack in client_list["StackSummaries"]:
    print("Deleting Stack: ",stack["StackName"])
    deleted = False
    toggleForceDelete = False

    cfn_client.update_termination_protection(EnableTerminationProtection=False, StackName=stack["StackName"])

    cfn_client.delete_stack(StackName = stack["StackName"])

    while (not deleted):
        
        try:
            stack_status = cfn_client.describe_stacks(StackName = stack["StackId"])["Stacks"][0]["StackStatus"]

            if (stack_status == "DELETE_FAILED" and not toggleForceDelete):
                cfn_client.delete_stack(StackName = stack["StackName"],
                                DeletionMode='FORCE_DELETE_STACK')
                toggleForceDelete = True
                print("Trying Force Delete...")
            elif (stack_status == "DELETE_COMPLETE"):
                deleted = True
                print("\nDeleted Stack: ", stack["StackName"], "\n")
            else:
                print('*', end='', flush=True)
                time.sleep(1) # Waiting to delete finish, check every 1 secs
        except Exception as e:
            print(e)
#endregion
"""

"""
#region Delete S3

s3_client = boto3.client('s3')

s3_list = s3_client.list_buckets()

for bucket in s3_list["Buckets"]:
    if ("aws-accelerator" in bucket["Name"] or "cdk-accel" in bucket["Name"]):

        print("Deleting S3: ", bucket["Name"])

        try:
            s3_client.delete_bucket(Bucket = bucket["Name"])
        except:
            theProblemBucket = s3_client.list_objects_v2(Bucket=bucket["Name"])
            for object in theProblemBucket['Contents']:
                #s3_client.delete_object(Bucket=bucket["Name"], Key=object['Key'])
                boto3.resource('s3').Bucket(bucket["Name"]).object_versions.filter(Prefix=object['Key']).delete()
            
            s3_client.delete_bucket(Bucket = bucket["Name"])

#endregion

"""

"""
#region Delete KMS

print("Deleting KMS keys")
kms_client = boto3.client("kms")

key_list = kms_client.list_keys()

for key in key_list["Keys"]:
    
    key_metadata = kms_client.describe_key(KeyId = key["KeyId"])["KeyMetadata"]
    
    if ( key_metadata["KeyState"] == "Enabled" ):
        #print("Scheduling Deletion of KMS Key: ", key["KeyArn"])

        try:
            kms_client.schedule_key_deletion(KeyId = key["KeyId"], PendingWindowInDays=7)
        except:
            1==1


#endregion
"""

"""
#region Delete ECR
print("Deleting ECR")
ecr_client = boto3.client("ecr")

ecr_list = ecr_client.describe_repositories()

for repo in ecr_list["repositories"]:
    ecr_client.delete_repository(repositoryName = repo['repositoryName'], force=True)

#endregion
"""



