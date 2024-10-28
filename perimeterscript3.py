import boto3
import json

# Initialize boto3 clients
ec2 = boto3.client("ec2")
s3 = boto3.client("s3")
iam = boto3.client("iam")

# Define resource names and values
bucket_name = "data-perimeter-demo-bucket-147997127509"
vpc_cidr = "10.0.0.0/16"
subnet_cidr = "10.0.1.0/24"
allowed_aws_account = "147997127509"  # Replace with the AWS account ID
role_name = "DataPerimeterRole"  # Replace with your role name
organization_id = "o-vflmjsfa5x"  # Replace with your Organization ID, if applicable

def create_vpc():
    vpc = ec2.create_vpc(CidrBlock=vpc_cidr)
    vpc_id = vpc['Vpc']['VpcId']
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})

    igw = ec2.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

    subnet = ec2.create_subnet(CidrBlock=subnet_cidr, VpcId=vpc_id)
    subnet_id = subnet['Subnet']['SubnetId']

    route_table = ec2.create_route_table(VpcId=vpc_id)
    route_table_id = route_table['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
    ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)

    return vpc_id, subnet_id, route_table_id, igw_id

def create_vpc_endpoint(vpc_id, route_table_id):
    # Define a valid VPC endpoint policy
    endpoint_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",  # Adjust if you want to restrict access further
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
    return endpoint_id

def create_bucket(bucket_name):
    s3.create_bucket(Bucket=bucket_name)

def apply_bucket_policy(bucket_name, endpoint_id, organization_id=None, allowed_aws_account=None):
    # Corrected to use IAM role ARN correctly
    role_arn = f"arn:aws:iam::{allowed_aws_account}:role/{role_name}"

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
            "Principal": {"AWS": role_arn},
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:sourceVpce": endpoint_id
                }
            }
        }
    ]

    if organization_id:
        policy_statements[1]["Condition"]["StringEquals"]["aws:PrincipalOrgID"] = organization_id

    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": policy_statements
    }

    s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))

def create_iam_role(role_name):
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
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role '{role_name}' already exists.")

# Cleanup functions
def delete_bucket(bucket_name):
    try:
        # Delete all objects and versions in the bucket
        bucket = s3.Bucket(bucket_name)
        bucket.object_versions.delete()
        s3.delete_bucket_policy(Bucket=bucket_name)
        s3.delete_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' and all its objects have been deleted.")
    except Exception as e:
        print(f"Error deleting bucket: {e}")

def delete_vpc(vpc_id, igw_id, endpoint_id, subnet_id, route_table_id):
    try:
        ec2.delete_vpc_endpoint(VpcEndpointId=endpoint_id)
        ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw_id)
        ec2.delete_subnet(SubnetId=subnet_id)
        ec2.delete_route_table(RouteTableId=route_table_id)
        ec2.delete_vpc(VpcId=vpc_id)
        print(f"VPC '{vpc_id}' and associated resources have been deleted.")
    except Exception as e:
        print(f"Error deleting VPC or its components: {e}")

def delete_iam_role(role_name):
    try:
        iam.delete_role(RoleName=role_name)
        print(f"Role '{role_name}' has been deleted.")
    except Exception as e:
        print(f"Error deleting IAM role: {e}")

# Run setup
vpc_id, subnet_id, route_table_id, igw_id = create_vpc()
endpoint_id = create_vpc_endpoint(vpc_id, route_table_id)
create_bucket(bucket_name)
create_iam_role(role_name)
apply_bucket_policy(bucket_name, endpoint_id, organization_id=organization_id, allowed_aws_account=allowed_aws_account)

# Uncomment to clean up resources after testing
# delete_bucket(bucket_name)
# delete_vpc(vpc_id, igw_id, endpoint_id, subnet_id, route_table_id)
# delete_iam_role(role_name)