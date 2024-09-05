import boto3
import time

session = boto3.Session()

auditRoleArn = "arn:aws:iam::841162688055:role/OrganizationAccountAccessRole"
logArchiveRoleArn = "arn:aws:iam::423623844928:role/OrganizationAccountAccessRole"
sharedRoleArn = "arn:aws:iam::474668387623:role/OrganizationAccountAccessRole"
networkRoleArn = "arn:aws:iam::147997127509:role/OrganizationAccountAccessRole"

def deleteCloudformation(session):
    cfn_client = session.client('cloudformation')

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

def deleteS3(session):
    s3_client = session.client('s3')

    s3_list = s3_client.list_buckets()

    for bucket in s3_list["Buckets"]:
        if ("aws-accelerator" in bucket["Name"] or "cdk-accel" in bucket["Name"]):

            print("Deleting S3: ", bucket["Name"])

            try:
                s3_client.delete_bucket(Bucket = bucket["Name"])
            except:
                theProblemBucket = s3_client.list_objects_v2(Bucket=bucket["Name"])
                print("Deleting Bucket Items ", end='', flush=True)
                for object in theProblemBucket['Contents']:
                    #s3_client.delete_object(Bucket=bucket["Name"], Key=object['Key'])
                    print("*", end='', flush=True)
                    session.resource('s3').Bucket(bucket["Name"]).object_versions.filter(Prefix=object['Key']).delete()
                
                s3_client.delete_bucket(Bucket = bucket["Name"])

def deleteKMS(session):
    #print("Checking KMS keys")
    kms_client = session.client("kms")

    key_list = kms_client.list_keys()

    for key in key_list["Keys"]:
        
        key_metadata = kms_client.describe_key(KeyId = key["KeyId"])["KeyMetadata"]
        
        if ( key_metadata["KeyState"] == "Enabled" ):
            print("Checking KMS Key: ", key["KeyArn"])

            try:
                kms_client.schedule_key_deletion(KeyId = key["KeyId"], PendingWindowInDays=7)
            except:
                1==1

def deleteECR(session):
    #print("Deleting ECR")
    ecr_client = session.client("ecr")

    ecr_list = ecr_client.describe_repositories()

    for repo in ecr_list["repositories"]:
        print("Deleting repo: ", repo["repositoryName"])
        ecr_client.delete_repository(repositoryName = repo['repositoryName'], force=True)

def deleteLogGroups(session):
    #print("Deleting Log Groups ")
    logs_client = session.client("logs")

    while (len(logs_client.describe_log_groups()["logGroups"]) > 0): 
        log_groups = logs_client.describe_log_groups()

        for log_group in log_groups["logGroups"]:
            print("Deleting Log Group: ", log_group["logGroupName"])
            logs_client.delete_log_group(logGroupName = log_group["logGroupName"])

def deleteIAMRoles(session):
    #print("Deleting IAM Roles: ")
    iam_client = session.client("iam")

    role_list = iam_client.list_roles()

    for role in role_list["Roles"]:

        if ("AWSAccelerator" in role["RoleName"] or "cdk-accel" in role["RoleName"]):
            print("Deleting Role: ", role["RoleName"])

            try:
                iam_client.delete_role(RoleName = role["RoleName"])
            except:
                
                try:
                    attached_policies = iam_client.list_attached_role_policies(RoleName = role["RoleName"])["AttachedPolicies"]

                    for policy in attached_policies:
                        print("Detaching Role Policy :" , policy["PolicyName"])
                        iam_client.detach_role_policy(RoleName = role["RoleName"], PolicyArn = policy["PolicyArn"])

                    iam_client.delete_role(RoleName = role["RoleName"])
                except:
                    attached_inline_policies = iam_client.list_role_policies(RoleName = role["RoleName"])["PolicyNames"]

                    for inlinepolicy in attached_inline_policies:
                        print("Deleting Inline Role Policy :" , inlinepolicy)
                        iam_client.delete_role_policy(RoleName = role["RoleName"], PolicyName = inlinepolicy)

                    iam_client.delete_role(RoleName = role["RoleName"])

def deleteLambdas(session):
    lambda_client = session.client("lambda")

    lambda_list = lambda_client.list_functions()

    for function in lambda_list["Functions"]:

        if ("AWSAccelerator" in function["FunctionName"]):
            print("Deleting Function: ", function["FunctionName"])

            lambda_client.delete_function(FunctionName = function["FunctionName"])

def deleteKinesis(session):
    kinesis_client = session.client("kinesis") 

    stream_list = kinesis_client.list_streams()

    for stream in stream_list["StreamNames"]:
        print("Deleting Kinesis Stream: ",stream)
        kinesis_client.delete_stream(StreamName = stream, EnforceConsumerDeletion = True)

def deleteFirehose(session):
    firehose_client = session.client("firehose")

    firehose_list = firehose_client.list_delivery_streams()

    for firehose in firehose_list["DeliveryStreamNames"]:
        print("Deleting Firehose Stream: ", firehose)
        firehose_client.delete_delivery_stream(DeliveryStreamName = firehose, AllowForceDelete = True)

def deleteAll(session):
    deleteCloudformation(session)
    deleteS3(session)
    deleteKMS(session)
    deleteECR(session)
    deleteLogGroups(session)
    deleteKinesis(session)
    deleteFirehose(session)
    deleteLambdas(session)
    deleteIAMRoles(session)

def assumeRole(RoleArn):
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=RoleArn,
        RoleSessionName="OrganizationAccountAccessRole")

    #print(assumed_role_object)
    credentials = assumed_role_object['Credentials']
    global session
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'])
    
    #s3 not working


deleteAll(boto3)

assumeRole(auditRoleArn)
deleteAll(session)

assumeRole(logArchiveRoleArn)
deleteAll(session)

assumeRole(sharedRoleArn)
deleteAll(session)

assumeRole(networkRoleArn)
deleteAll(session)

