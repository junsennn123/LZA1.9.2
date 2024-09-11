/**
 *  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { AcceleratorStack, AcceleratorStackProps } from './accelerator-stack';

import { Bucket, BucketEncryptionType } from '@aws-accelerator/constructs';

export class AddBucketStack extends AcceleratorStack {
  constructor(scope: Construct, id: string, props: AcceleratorStackProps) {
    super(scope, id, props);

    if (
      cdk.Stack.of(this).region === props.globalConfig.homeRegion &&
      cdk.Stack.of(this).account === props.accountsConfig.getManagementAccountId()
    ) {
      const addBucketTest = new Bucket(this, 'addBucketTest', {
        s3BucketName: `${this.acceleratorResourceNames.bucketPrefixes.addBucket}-${cdk.Stack.of(this).account}-${
          cdk.Stack.of(this).region
        }`,
        encryptionType: this.isS3CMKEnabled ? BucketEncryptionType.SSE_KMS : BucketEncryptionType.SSE_S3,
      });

      //addBucketTest.getS3Bucket().grantRead();

      addBucketTest.getKey();
    }
  }
}
