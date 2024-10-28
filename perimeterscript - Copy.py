import boto3
import json

# Initialize boto3 clients
ec2 = boto3.client("ec2")
s3 = boto3.client("s3")
iam = boto3.client("iam")

# Define resource names and values
bucket_name = "data-perimeter-demo-bucket-tester"
vpc_cidr = "115.66.0.0/16"
subnet_cidr = "115.66.91.0/24"
allowed_aws_account = "account-id"  # Replace with the AWS account ID
role_name = "DataPerimeterRole"  # Replace with your role name
organization_id = "o-orgID"  # Replace with your Organization ID, if applicable

def create_vpc():
    # Create VPC
    vpc = ec2.create_vpc(CidrBlock=vpc_cidr)
    vpc_id = vpc['Vpc']['VpcId']
    print(f"Created VPC: {vpc_id}")

    # Enable DNS support and hostnames
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})

    # Create an Internet Gateway and attach it to the VPC
    igw = ec2.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Attached Internet Gateway: {igw_id}")

    # Create a public subnet in the VPC
    subnet = ec2.create_subnet(CidrBlock=subnet_cidr, VpcId=vpc_id)
    subnet_id = subnet['Subnet']['SubnetId']
    print(f"Created Subnet: {subnet_id}")

    # Create a route table and associate it with the subnet
    route_table = ec2.create_route_table(VpcId=vpc_id)
    route_table_id = route_table['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
    ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
    print(f"Created and associated Route Table: {route_table_id}")

    return vpc_id, subnet_id, route_table_id

def create_vpc_endpoint(vpc_id, route_table_id):
    # Create an S3 VPC Endpoint with a restrictive policy
    endpoint_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:SourceVpc": vpc_id
                    }
                }
            }
        ]
    }

    endpoint = ec2.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName="com.amazonaws.us-east-1.s3",  # Use the appropriate region's endpoint
        VpcEndpointType="Gateway",
        RouteTableIds=[route_table_id],
        PolicyDocument=json.dumps(endpoint_policy)
    )
    endpoint_id = endpoint['VpcEndpoint']['VpcEndpointId']
    print(f"Created VPC Endpoint with policy: {endpoint_id}")
    return endpoint_id

def create_bucket(bucket_name):
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    except Exception as e:
        print(f"Error creating bucket: {e}")

def apply_bucket_policy(bucket_name, endpoint_id, organization_id=None, allowed_aws_account=None):
    # Define the bucket policy to allow access only from the specified VPC endpoint and trusted IAM role
    
    #role_arn = f"arn:aws:iam::{allowed_aws_account}"

    policy_statements = [
        {
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:sourceVpce": endpoint_id
                }
            }
        },
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:sourceVpce": endpoint_id,
                    "aws:PrincipalOrgID": organization_id
                }
            }
        }
    ]

    # Add an optional restriction for Organization ID if specified
    if organization_id:
        policy_statements[1]["Condition"]["StringEquals"]["aws:PrincipalOrgID"] = organization_id

    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": policy_statements
    }

    # Convert the policy to JSON and apply it to the bucket
    bucket_policy_json = json.dumps(bucket_policy)

    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_json)
        print(f"Policy applied to bucket '{bucket_name}'.")
    except Exception as e:
        print(f"Error applying policy: {e}")

def create_iam_role(role_name):
    # Trust policy allowing the role to be assumed only within the specific account
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        print(f"Created IAM Role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role '{role_name}' already exists.")

# Run the script
vpc_id, subnet_id, route_table_id = create_vpc()
endpoint_id = create_vpc_endpoint(vpc_id, route_table_id)
create_bucket(bucket_name)
create_iam_role(role_name)
apply_bucket_policy(bucket_name, endpoint_id, organization_id=organization_id, allowed_aws_account=allowed_aws_account)
